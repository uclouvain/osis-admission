# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

from copy import copy

from django.db import transaction
from django.utils.functional import cached_property
from django.views.generic import FormView

from admission.ddd import REGIMES_LINGUISTIQUES_SANS_TRADUCTION, PLUS_5_ISO_CODES
from admission.ddd.admission.domain.model.formation import est_formation_medecine_ou_dentisterie
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.formation_generale.domain.model.enums import CHOIX_DIPLOME_OBTENU
from admission.forms.admission.education import (
    BachelorAdmissionEducationBelgianDiplomaForm,
    BachelorAdmissionEducationForeignDiplomaForm,
    BachelorAdmissionEducationForm,
    BaseAdmissionEducationForm,
)
from admission.infrastructure.admission.domain.service.profil_candidat import ProfilCandidatTranslator
from admission.views.common.mixins import LoadDossierViewMixin, AdmissionFormMixin
from base.models.enums.education_group_types import TrainingType
from base.models.enums.got_diploma import GotDiploma
from osis_profile.models import BelgianHighSchoolDiploma, ForeignHighSchoolDiploma, HighSchoolDiplomaAlternative
from osis_profile.models.enums.education import (
    BelgianCommunitiesOfEducation,
    HighSchoolDiplomaTypes,
    Equivalence,
    ForeignDiplomaTypes,
)

__all__ = [
    'AdmissionEducationFormView',
]


class AdmissionEducationFormView(AdmissionFormMixin, LoadDossierViewMixin, FormView):
    urlpatterns = 'education'
    template_name = 'admission/forms/education.html'
    forms = None
    specific_questions_tab = Onglets.ETUDES_SECONDAIRES
    extra_context = {
        'without_menu': True,
    }
    update_requested_documents = True
    update_admission_author = True
    permission_required = 'admission.change_admission_secondary_studies'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        if self.is_bachelor:
            context_data.update(self.get_forms(context_data))
            context_data['foreign_diploma_type_images'] = {
                'INTERNATIONAL_BACCALAUREATE': 'img/IBO.png',
                'EUROPEAN_BACHELOR': 'img/schola_europa.png',
            }
            context_data['linguistic_regimes_without_translation'] = list(REGIMES_LINGUISTIQUES_SANS_TRADUCTION)
            context_data['is_med_dent_training'] = self.is_med_dent_training
            context_data['is_vae_potential'] = self.high_school_diploma['is_vae_potential']
            context_data['plus_5_iso_codes'] = list(PLUS_5_ISO_CODES)
        return context_data

    @cached_property
    def is_bachelor(self):
        return self.proposition.formation.type == TrainingType.BACHELOR.name

    @cached_property
    def high_school_diploma(self):
        return {
            'graduated_from_high_school': self.admission.candidate.graduated_from_high_school,
            'graduated_from_high_school_year': self.admission.candidate.graduated_from_high_school_year,
            'belgian_diploma': getattr(self.admission.candidate, 'belgianhighschooldiploma', None),
            'foreign_diploma': getattr(self.admission.candidate, 'foreignhighschooldiploma', None),
            'high_school_diploma_alternative': getattr(self.admission.candidate, 'highschooldiplomaalternative', None),
            'specific_question_answers': self.admission.specific_question_answers,
            'is_vae_potential': ProfilCandidatTranslator.est_potentiel_vae(self.admission.candidate.global_id),
        }

    def get_template_names(self):
        if self.is_bachelor:
            return ['admission/forms/bachelor_education.html']
        return ['admission/forms/education.html']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['form_item_configurations'] = self.specific_questions
        return kwargs

    def get_form_class(self):
        return BachelorAdmissionEducationForm if self.is_bachelor else BaseAdmissionEducationForm

    @cached_property
    def is_med_dent_training(self):
        return est_formation_medecine_ou_dentisterie(self.proposition.formation.code_domaine)

    def get_initial(self):
        return self.high_school_diploma

    @staticmethod
    def check_bound_and_set_required_attr(form):
        """Check if the passed form is bound. If it is, it means that we can set the use_required_attribute to False
        for form validation."""
        if form.is_bound:
            form.empty_permitted = False

    def post(self, request, *args, **kwargs):
        if not self.is_bachelor:
            # Default behavior as we have a single form
            return super().post(request, *args, **kwargs)

        # Custom behavior as we have multiple forms
        forms = self.get_forms()

        main_form = forms['main_form']
        belgian_diploma_form = forms['belgian_diploma_form']
        foreign_diploma_form = forms['foreign_diploma_form']

        self.check_bound_and_set_required_attr(belgian_diploma_form)
        self.check_bound_and_set_required_attr(foreign_diploma_form)

        # Page is valid if all bound forms are valid
        if all(not form.is_bound or form.is_valid() for form in forms.values()):
            return self.form_valid(main_form)
        return self.form_invalid(main_form)

    def form_valid(self, form):
        # Prepare data
        validated_data = self.prepare_data(copy(form.cleaned_data))
        candidate = self.admission.candidate

        with transaction.atomic():
            # Save data
            candidate.graduated_from_high_school = validated_data.get('graduated_from_high_school')
            candidate.graduated_from_high_school_year = validated_data.get('graduated_from_high_school_year')
            candidate.save()

            belgian_diploma_data = validated_data.get('belgian_diploma')
            foreign_diploma_data = validated_data.get('foreign_diploma')
            high_school_diploma_alternative_data = validated_data.get('high_school_diploma_alternative')

            # For bachelor admissions
            if belgian_diploma_data:
                self.update_belgian_diploma(belgian_diploma_data)
            elif foreign_diploma_data:
                self.update_foreign_diploma(foreign_diploma_data)
            elif high_school_diploma_alternative_data:
                self.update_high_school_diploma_alternative(high_school_diploma_alternative_data)
            else:
                # For other admissions
                if candidate.graduated_from_high_school not in CHOIX_DIPLOME_OBTENU:
                    # Clean existing diplomas as we indicate now that there is no one
                    self.clean_belgian_diploma()
                    self.clean_foreign_diploma()
                else:
                    # Update existing diplomas
                    for diploma_type in ['belgian_diploma', 'foreign_diploma']:
                        diploma = self.high_school_diploma[diploma_type]
                        if diploma and diploma.academic_graduation_year != candidate.graduated_from_high_school_year:
                            diploma.academic_graduation_year = candidate.graduated_from_high_school_year
                            diploma.save(update_fields=['academic_graduation_year'])

                # Clean alternative high school diploma as we indicate now that it's not the case
                if candidate.graduated_from_high_school != GotDiploma.NO.name:
                    self.clean_high_school_diploma_alternative()

        return super().form_valid(form)

    def update_current_admission_on_form_valid(self, form, admission):
        admission.specific_question_answers = form.cleaned_data['specific_question_answers'] or {}

    def get_forms(self, context_data=None):
        if context_data is None:
            context_data = {}

        if not self.forms:
            kwargs = self.get_form_kwargs()
            data = kwargs.pop('data', None)
            # We don't work with files on those forms
            kwargs.pop('files', None)
            kwargs.pop('prefix')
            initial = kwargs.pop('initial')
            kwargs.pop('form_item_configurations')

            graduated_from_high_school = data and data.get('graduated_from_high_school') in CHOIX_DIPLOME_OBTENU
            got_belgian_diploma = (
                graduated_from_high_school and data.get('diploma_type') == HighSchoolDiplomaTypes.BELGIAN.name
            )
            got_foreign_diploma = (
                graduated_from_high_school and data.get('diploma_type') == HighSchoolDiplomaTypes.FOREIGN.name
            )

            self.forms = {
                'main_form': context_data.pop('form') if 'form' in context_data else self.get_form(),
                'belgian_diploma_form': BachelorAdmissionEducationBelgianDiplomaForm(
                    prefix='belgian_diploma',
                    instance=initial.get('belgian_diploma'),
                    empty_permitted=True,
                    use_required_attribute=False,
                    # don't send data to prevent validation
                    data=data if data and got_belgian_diploma else None,
                    **kwargs,
                ),
                'foreign_diploma_form': BachelorAdmissionEducationForeignDiplomaForm(
                    prefix='foreign_diploma',
                    instance=initial.get('foreign_diploma'),
                    empty_permitted=True,
                    use_required_attribute=False,
                    is_med_dent_training=self.is_med_dent_training,
                    # don't send data to prevent validation
                    data=data if data and got_foreign_diploma else None,
                    **kwargs,
                ),
            }
        return self.forms

    @staticmethod
    def prepare_diploma(data, forms, diploma):
        data[diploma] = forms['{}_form'.format(diploma)].cleaned_data
        data[diploma]['academic_graduation_year'] = data.get('graduated_from_high_school_year')
        data[diploma]['high_school_diploma'] = data.pop('high_school_diploma')

    def prepare_data(self, main_form_data):
        # General education (except bachelor) and continuing education admission
        if not self.is_bachelor:
            return main_form_data

        # Bachelor admission
        forms = self.get_forms()
        for form in forms.values():
            form.is_valid()

        data = forms['main_form'].cleaned_data

        graduated_from_high_school = data.get('graduated_from_high_school')

        first_cycle_admission_exam = data.pop('first_cycle_admission_exam', [])
        if graduated_from_high_school == GotDiploma.NO.name:
            return {
                'specific_question_answers': data.get('specific_question_answers'),
                'graduated_from_high_school': graduated_from_high_school,
                'graduated_from_high_school_year': data.get('graduated_from_high_school_year'),
                'high_school_diploma_alternative': {'first_cycle_admission_exam': first_cycle_admission_exam},
            }

        # The candidate has a diploma or will have one this year

        if data.pop('diploma_type') == HighSchoolDiplomaTypes.BELGIAN.name:
            self.prepare_diploma(data, forms, 'belgian_diploma')
            belgian_diploma = data.get('belgian_diploma')
            belgian_diploma.pop('has_other_educational_type')

            if belgian_diploma.get('community') != BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name:
                belgian_diploma['educational_type'] = ''
                belgian_diploma['educational_other'] = ''

            if belgian_diploma.pop('other_institute'):
                belgian_diploma['institute'] = None
            else:
                belgian_diploma['other_institute_name'] = ''
                belgian_diploma['other_institute_address'] = ''

        else:
            self.prepare_diploma(data, forms, 'foreign_diploma')
            foreign_diploma_data = data.get('foreign_diploma')

            is_bachelor = foreign_diploma_data.get('foreign_diploma_type') == ForeignDiplomaTypes.NATIONAL_BACHELOR.name
            equivalence_ue_country = (
                foreign_diploma_data.get('country')
                and foreign_diploma_data['country'].european_union
                or self.is_med_dent_training
            )

            # Define and clean main form fields
            # Clean equivalence fields
            if not is_bachelor or not equivalence_ue_country:
                foreign_diploma_data['equivalence'] = ''

            if not is_bachelor or equivalence_ue_country:
                foreign_diploma_data['final_equivalence_decision_not_ue'] = []

            if (
                not is_bachelor
                or not equivalence_ue_country
                or foreign_diploma_data['equivalence'] != Equivalence.PENDING.name
            ):
                foreign_diploma_data['equivalence_decision_proof'] = []

            if (
                not is_bachelor
                or not equivalence_ue_country
                or foreign_diploma_data['equivalence'] != Equivalence.YES.name
            ):
                foreign_diploma_data['final_equivalence_decision_ue'] = []

            # Clean fields depending on the linguistic regime
            if foreign_diploma_data.get('linguistic_regime'):
                foreign_diploma_data['other_linguistic_regime'] = ''

                if foreign_diploma_data.get('linguistic_regime').code in REGIMES_LINGUISTIQUES_SANS_TRADUCTION:
                    foreign_diploma_data['high_school_transcript_translation'] = []
                    foreign_diploma_data['high_school_diploma_translation'] = []

        return data

    def update_belgian_diploma(self, belgian_diploma_data):
        BelgianHighSchoolDiploma.objects.update_or_create(
            person=self.admission.candidate,
            defaults=belgian_diploma_data,
        )
        self.clean_foreign_diploma()
        self.clean_high_school_diploma_alternative()

    def update_foreign_diploma(self, foreign_diploma_data):
        ForeignHighSchoolDiploma.objects.update_or_create(
            person=self.admission.candidate,
            defaults=foreign_diploma_data,
        )
        self.clean_belgian_diploma()
        self.clean_high_school_diploma_alternative()

    def update_high_school_diploma_alternative(self, high_school_diploma_alternative_data):
        HighSchoolDiplomaAlternative.objects.update_or_create(
            person=self.admission.candidate,
            defaults=high_school_diploma_alternative_data,
        )
        self.clean_belgian_diploma()
        self.clean_foreign_diploma()

    def clean_foreign_diploma(self):
        if self.high_school_diploma['foreign_diploma']:
            self.high_school_diploma['foreign_diploma'].delete()

    def clean_belgian_diploma(self):
        if self.high_school_diploma['belgian_diploma']:
            self.high_school_diploma['belgian_diploma'].delete()

    def clean_high_school_diploma_alternative(self):
        if self.high_school_diploma['high_school_diploma_alternative']:
            self.high_school_diploma['high_school_diploma_alternative'].delete()

    def get_success_url(self):
        return self.request.get_full_path()
