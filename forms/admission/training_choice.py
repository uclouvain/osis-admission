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
from contextlib import suppress
from typing import Optional

from dal import autocomplete, forward
from django import forms
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from admission.models import Scholarship
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import (
    COMMISSIONS_CDE_CLSM,
    COMMISSIONS_CDSS,
    SIGLES_SCIENCES,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
)
from admission.ddd.admission.doctorat.preparation.dtos import DoctoratDTO
from admission.ddd.admission.doctorat.preparation.dtos.proposition import (
    PropositionGestionnaireDTO as PropositionDoctoraleDTO,
)
from admission.ddd.admission.domain.enums import TypeFormation
from admission.ddd.admission.enums import TypeBourse
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixMoyensDecouverteFormation
from admission.ddd.admission.formation_continue.dtos import PropositionDTO as PropositionContinueDTO
from admission.ddd.admission.formation_generale.dtos.proposition import (
    PropositionGestionnaireDTO as PropositionGeneraleDTO,
)
from admission.forms import get_scholarship_choices, format_training, AdmissionMainCampusChoiceField
from admission.forms.specific_question import ConfigurableFormMixin
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from admission.views.autocomplete.trainings import ContinuingManagedEducationTrainingsAutocomplete
from base.forms.utils import FIELD_REQUIRED_MESSAGE, EMPTY_CHOICE
from base.forms.utils.academic_year_field import AcademicYearModelChoiceField
from base.forms.utils.fields import RadioBooleanField
from base.models.education_group_year import EducationGroupYear
from base.models.enums.state_iufc import StateIUFC


class BaseTrainingChoiceForm(ConfigurableFormMixin):
    training_type = forms.ChoiceField(
        choices=TypeFormation.choices(),
        label=_('Course type'),
        disabled=True,
        required=False,
    )

    campus = AdmissionMainCampusChoiceField(
        label=_('Campus (optional)'),
        required=False,
        queryset=None,
        to_field_name='uuid',
    )


class GeneralTrainingChoiceForm(BaseTrainingChoiceForm):
    general_education_training = forms.ChoiceField(
        label=pgettext_lazy('admission', 'Course'),
        disabled=True,
        required=False,
    )

    has_double_degree_scholarship = RadioBooleanField(
        label=_('Are you a dual degree student?'),
        required=False,
        help_text=_(
            'Dual degrees involve joint coursework between two or more universities, leading to two separate diplomas '
            'awarded by each signatory university.'
        ),
    )

    double_degree_scholarship = forms.CharField(
        required=False,
        widget=autocomplete.ListSelect2,
    )

    has_international_scholarship = RadioBooleanField(
        label=_('Do you have an international scholarship?'),
        required=False,
        help_text=_(
            'An international scholarship may be awarded to students as part of a project. These international '
            'grants are awarded by ARES and a scholarship certificate must be provided.'
        ),
    )

    international_scholarship = forms.CharField(
        required=False,
        widget=autocomplete.ListSelect2,
    )

    has_erasmus_mundus_scholarship = RadioBooleanField(
        label=_('Are you an Erasmus Mundus student?'),
        required=False,
        help_text=_(
            'Erasmus Mundus is a study abroad programme devised by an international partnership of higher '
            'education institutions. Scholarships are awarded to students and proof of funding is therefore required.'
        ),
    )

    erasmus_mundus_scholarship = forms.CharField(
        required=False,
        widget=autocomplete.ListSelect2,
    )

    def __init__(self, proposition: PropositionGeneraleDTO, user: User, *args, **kwargs):
        self.training_type = AnneeInscriptionFormationTranslator.ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE[
            proposition.formation.type
        ]

        kwargs['initial'] = {
            'campus': proposition.formation.campus.uuid if proposition.formation.campus else '',
            'training_type': self.training_type,
            'double_degree_scholarship': proposition.bourse_double_diplome and proposition.bourse_double_diplome.uuid,
            'international_scholarship': proposition.bourse_internationale and proposition.bourse_internationale.uuid,
            'erasmus_mundus_scholarship': proposition.bourse_erasmus_mundus and proposition.bourse_erasmus_mundus.uuid,
            'general_education_training': proposition.formation.sigle,
            'specific_question_answers': proposition.reponses_questions_specifiques,
        }

        super().__init__(*args, **kwargs)

        self.fields['campus'].disabled = True

        self.fields['general_education_training'].choices = [
            [self.initial['general_education_training'], mark_safe(format_training(proposition.formation))]
        ]

        scholarships = (
            Scholarship.objects.filter(disabled=False).order_by('long_name', 'short_name')
            if self.training_type == TypeFormation.MASTER.name
            else []
        )

        self.scholarship_fields = [
            ['double_degree_scholarship', TypeBourse.DOUBLE_TRIPLE_DIPLOMATION],
            ['international_scholarship', TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE],
            ['erasmus_mundus_scholarship', TypeBourse.ERASMUS_MUNDUS],
        ]

        for scholarship_field, scholarship_type in self.scholarship_fields:
            self.initial[f'has_{scholarship_field}'] = bool(self.initial.get(scholarship_field))
            self.fields[scholarship_field].choices = get_scholarship_choices(
                scholarships=scholarships,
                scholarship_type=scholarship_type,
            )
            self.fields[scholarship_field].widget.choices = self.fields[scholarship_field].choices

    def clean(self):
        cleaned_data = super().clean()
        self.clean_master_scholarships(cleaned_data)
        return cleaned_data

    def clean_master_scholarships(self, cleaned_data):
        if self.training_type == TypeFormation.MASTER.name:
            for scholarship_field, _ in self.scholarship_fields:
                if cleaned_data.get(f'has_{scholarship_field}'):
                    if not cleaned_data.get(scholarship_field):
                        self.add_error(scholarship_field, FIELD_REQUIRED_MESSAGE)
                else:
                    cleaned_data[scholarship_field] = ''

                    if cleaned_data.get(f'has_{scholarship_field}') is None:
                        self.add_error(f'has_{scholarship_field}', FIELD_REQUIRED_MESSAGE)

        else:
            for scholarship_field, _ in self.scholarship_fields:
                cleaned_data[scholarship_field] = ''
                cleaned_data[f'has_{scholarship_field}'] = ''

    class Media:
        js = ('js/dependsOn.min.js',)


class ContinuingTrainingChoiceForm(BaseTrainingChoiceForm):
    continuing_education_training = forms.ChoiceField(
        label=pgettext_lazy('admission', 'Course'),
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:continuing-managed-education-trainings",
            attrs={
                'data-placeholder': _('Acronym / Title'),
                'data-html': 'true',
            },
            forward=['academic_year', 'campus', forward.Const('uuid', 'id_field')],
        ),
    )

    academic_year = AcademicYearModelChoiceField(
        label=_('Academic year'),
        required=False,
        to_field_name='year',
    )

    motivations = forms.CharField(
        label=_('Motivations'),
        widget=forms.Textarea(
            attrs={
                'rows': 6,
            }
        ),
        max_length=1000,
        required=False,
    )

    ways_to_find_out_about_the_course = forms.MultipleChoiceField(
        label=_('How did you hear about this course?'),
        required=False,
        choices=ChoixMoyensDecouverteFormation.choices(),
        widget=forms.CheckboxSelectMultiple,
    )

    other_way_to_find_out_about_the_course = forms.CharField(
        label='',
        max_length=1000,
        required=False,
        widget=forms.TextInput(
            attrs={
                'aria-label': _('How else did you hear about this course?'),
            },
        ),
    )

    interested_mark = forms.NullBooleanField(
        label=_('Yes, I am interested in this course'),
        required=False,
        widget=forms.CheckboxInput,
    )

    class Media:
        js = ('js/dependsOn.min.js',)

    def __init__(self, proposition: PropositionContinueDTO, user: User, *args, **kwargs):
        self.training_type = AnneeInscriptionFormationTranslator.ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE[
            proposition.formation.type
        ]

        kwargs['initial'] = {
            'campus': proposition.formation.campus.uuid if proposition.formation.campus else '',
            'training_type': self.training_type,
            'continuing_education_training': proposition.formation.sigle,
            'academic_year': proposition.annee_demande,
            'interested_mark': proposition.marque_d_interet,
            'ways_to_find_out_about_the_course': proposition.moyens_decouverte_formation,
            'other_way_to_find_out_about_the_course': proposition.autre_moyen_decouverte_formation,
            'motivations': proposition.motivations,
            'specific_question_answers': proposition.reponses_questions_specifiques,
        }

        super().__init__(*args, **kwargs)

        if self.is_bound:
            selected_training = self.data.get(self.add_prefix('continuing_education_training'))
            selected_year = self.data.get(self.add_prefix('academic_year'))
        else:
            selected_training = self.initial.get('continuing_education_training')
            selected_year = self.initial.get('academic_year')

        self.continuing_training: Optional[EducationGroupYear] = None
        self.display_long_continuing_fields = False
        self.display_closed_continuing_fields = False

        if selected_training and selected_year:
            with suppress(EducationGroupYear.DoesNotExist):
                self.continuing_training = ContinuingManagedEducationTrainingsAutocomplete.get_base_queryset(
                    user=user,
                    acronyms=[selected_training],
                    academic_year=selected_year,
                ).get()

                self.display_long_continuing_fields = self.continuing_training.registration_required
                self.display_closed_continuing_fields = self.continuing_training.state == StateIUFC.CLOSED.name

        self.fields['continuing_education_training'].choices = [
            (
                selected_training,
                self.continuing_training.formatted_title  # type: ignore
                if self.continuing_training
                else selected_training,
            )
        ]

    def clean(self):
        cleaned_data = super().clean()
        self.clean_continuing_education(cleaned_data)
        return cleaned_data

    def clean_continuing_education(self, cleaned_data):
        for required_field in [
            'continuing_education_training',
            'motivations',
            'academic_year',
        ]:
            if not cleaned_data.get(required_field):
                self.add_error(required_field, FIELD_REQUIRED_MESSAGE)

        if (
            self.cleaned_data.get('academic_year')
            and self.cleaned_data.get('continuing_education_training')
            and not self.continuing_training
        ):
            self.add_error(
                'continuing_education_training',
                _('The selected training has not been found for this year.'),
            )

        if self.display_long_continuing_fields:
            if not cleaned_data.get('ways_to_find_out_about_the_course'):
                self.add_error('ways_to_find_out_about_the_course', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['ways_to_find_out_about_the_course'] = []

        if not self.display_closed_continuing_fields:
            cleaned_data['interested_mark'] = None

        if (
            cleaned_data.get('ways_to_find_out_about_the_course')
            and ChoixMoyensDecouverteFormation.AUTRE.name in cleaned_data['ways_to_find_out_about_the_course']
        ):
            if not cleaned_data.get('other_way_to_find_out_about_the_course'):
                self.add_error('other_way_to_find_out_about_the_course', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['other_way_to_find_out_about_the_course'] = ''


class DoctorateTrainingChoiceForm(BaseTrainingChoiceForm):
    admission_type = forms.ChoiceField(
        choices=ChoixTypeAdmission.choices(),
        initial=ChoixTypeAdmission.ADMISSION.name,
        label=_('Admission type'),
        widget=forms.RadioSelect,
    )

    justification = forms.CharField(
        label=_("Brief justification"),
        widget=forms.Textarea(
            attrs={
                'rows': 2,
                'placeholder': _("Reasons for provisional admission."),
            }
        ),
        required=False,
    )

    sector = forms.ChoiceField(
        label=_('Sector'),
        required=False,
        disabled=True,
    )

    doctorate_training = forms.ChoiceField(
        label=pgettext_lazy('admission', 'Course'),
        disabled=True,
    )

    proximity_commission_cde = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixCommissionProximiteCDEouCLSM.choices(),
        required=False,
    )

    proximity_commission_cdss = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixCommissionProximiteCDSS.choices(),
        required=False,
    )

    science_sub_domain = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixSousDomaineSciences.choices(),
        required=False,
    )

    @classmethod
    def get_proximity_commission_field(cls, training: DoctoratDTO) -> Optional[str]:
        """Determine the proximity commission field name for a given training."""
        if training.sigle_entite_gestion in COMMISSIONS_CDE_CLSM:
            return 'proximity_commission_cde'
        elif training.sigle_entite_gestion in COMMISSIONS_CDSS:
            return 'proximity_commission_cdss'
        elif training.sigle in SIGLES_SCIENCES:
            return 'science_sub_domain'

    class Media:
        js = ('js/dependsOn.min.js',)

    def __init__(self, proposition: PropositionDoctoraleDTO, user: User, *args, **kwargs):
        self.training_type = AnneeInscriptionFormationTranslator.ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE[
            proposition.doctorat.type
        ]

        kwargs['initial'] = {
            'campus': proposition.formation.campus.uuid if proposition.formation.campus else '',
            'training_type': self.training_type,
            'doctorate_training': proposition.doctorat.sigle,
            'specific_question_answers': proposition.reponses_questions_specifiques,
            'justification': proposition.justification,
            'sector': proposition.code_secteur_formation,
            'admission_type': proposition.type_admission,
        }

        self.proximity_commission_field = self.get_proximity_commission_field(proposition.doctorat)

        if proposition.commission_proximite and self.proximity_commission_field:
            kwargs['initial'][self.proximity_commission_field] = proposition.commission_proximite

        super().__init__(*args, **kwargs)

        self.fields['campus'].disabled = True

        # Initialise the choice fields
        self.fields['doctorate_training'].choices = [
            [self.initial['doctorate_training'], mark_safe(format_training(proposition.formation))]
        ]
        self.fields['sector'].choices = [[self.initial['sector'], proposition.intitule_secteur_formation]]

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('admission_type') == ChoixTypeAdmission.PRE_ADMISSION.name:
            if not cleaned_data.get('justification'):
                self.add_error('justification', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['justification'] = ''

        for field in [
            'proximity_commission_cde',
            'proximity_commission_cdss',
            'science_sub_domain',
        ]:
            if field == self.proximity_commission_field:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data[field] = ''
