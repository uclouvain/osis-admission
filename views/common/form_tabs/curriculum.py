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

import calendar
import datetime
import uuid
from decimal import Decimal
from typing import Union

from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch, F, ProtectedError, QuerySet
from django.forms import forms
from django.shortcuts import redirect, get_object_or_404
from django.template import loader
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, DeleteView

from admission.contrib.models.base import (
    AdmissionEducationalValuatedExperiences,
    BaseAdmission,
    AdmissionProfessionalValuatedExperiences,
)
from admission.contrib.models.checklist import FreeAdditionalApprovalCondition
from admission.ddd.admission.domain.service.verifier_curriculum import VerifierCurriculum
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.exports.admission_recap.constants import CURRICULUM_ACTIVITY_LABEL
from admission.forms.admission.curriculum import (
    AdmissionCurriculumAcademicExperienceForm,
    MINIMUM_CREDIT_NUMBER,
    AdmissionCurriculumEducationalExperienceYearFormSet,
    AdmissionCurriculumProfessionalExperienceForm,
)
from admission.forms.specific_question import ConfigurableFormMixin
from admission.utils import copy_documents
from admission.views.doctorate.mixins import AdmissionFormMixin, LoadDossierViewMixin
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.models.academic_year import AcademicYear
from base.models.enums.community import CommunityEnum
from osis_profile import BE_ISO_CODE, REGIMES_LINGUISTIQUES_SANS_TRADUCTION
from osis_profile.forms import (
    FORM_SET_PREFIX, FOLLOWING_FORM_SET_PREFIX, OSIS_DOCUMENT_UPLOADER_CLASS_PREFIX,
    OSIS_DOCUMENT_UPLOADER_CLASS,
)
from osis_profile.models import EducationalExperience, EducationalExperienceYear, ProfessionalExperience
from osis_profile.models.enums.curriculum import TranscriptType, EvaluationSystem, Result
from reference.models.enums.cycle import Cycle

__all__ = [
    'CurriculumEducationalExperienceFormView',
    'CurriculumEducationalExperienceDeleteView',
    'CurriculumEducationalExperienceDuplicateView',
    'CurriculumGlobalFormView',
    'CurriculumNonEducationalExperienceFormView',
    'CurriculumNonEducationalExperienceDeleteView',
    'CurriculumNonEducationalExperienceDuplicateView',
]


class CurriculumGlobalFormView(AdmissionFormMixin, LoadDossierViewMixin, FormView):
    urlpatterns = {'global': ''}
    template_name = 'admission/forms/curriculum.html'
    permission_required = 'admission.change_admission_curriculum'
    form_class = ConfigurableFormMixin
    update_requested_documents = True
    update_admission_author = True
    specific_questions_tab = Onglets.CURRICULUM

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['form_item_configurations'] = self.specific_questions
        return kwargs

    def get_initial(self):
        return {'specific_question_answers': self.admission.specific_question_answers}

    def update_current_admission_on_form_valid(self, form, admission):
        admission.specific_question_answers = form.cleaned_data['specific_question_answers'] or {}

    def get_success_url(self):
        return self.request.get_full_path()


class CurriculumEducationalExperienceFormView(AdmissionFormMixin, LoadDossierViewMixin, FormView):
    urlpatterns = {
        'educational': 'educational/<uuid:experience_uuid>',
        'educational_create': 'educational/create',
    }
    template_name = 'admission/forms/curriculum_educational_experience.html'
    permission_required = 'admission.change_admission_curriculum'
    form_class = forms.Form
    extra_context = {
        'without_menu': True,
    }
    update_requested_documents = True
    update_admission_author = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.existing_experience = False
        self._experience_id = None

    @property
    def experience_id(self):
        return self._experience_id or self.kwargs.get('experience_uuid', None)

    @cached_property
    def educational_experience(self) -> EducationalExperience:
        if self.experience_id:
            try:
                experience = (
                    EducationalExperience.objects.select_related(
                        'country',
                        'institute',
                        'program',
                        'fwb_equivalent_program',
                        'linguistic_regime',
                    )
                    .prefetch_related(
                        Prefetch(
                            'educationalexperienceyear_set',
                            queryset=EducationalExperienceYear.objects.select_related('academic_year'),
                        ),
                    )
                    .get(uuid=self.experience_id, person=self.admission.candidate)
                )
                self.existing_experience = True
                return experience
            except EducationalExperience.DoesNotExist:
                messages.error(self.request, _('Educational experience not found.'))

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        educational_experience = self.educational_experience
        all_educational_experience_years = None
        start = None
        end = None

        if self.existing_experience:
            all_years_config = self.get_educational_experience_year_set_with_lost_years(
                educational_experience.educationalexperienceyear_set.all().values(
                    'registered_credit_number',
                    'acquired_credit_number',
                    'result',
                    'transcript',
                    'transcript_translation',
                    'with_block_1',
                    'with_complement',
                    'fwb_registered_credit_number',
                    'fwb_acquired_credit_number',
                    'reduction',
                    'is_102_change_of_course',
                    year=F('academic_year__year'),
                ),
            )
            all_educational_experience_years = all_years_config['educational_experience_year_set_with_lost_years']
            start = all_years_config['start']
            end = all_years_config['end']

        current_academic_year = AcademicYear.objects.current()

        base_form = AdmissionCurriculumAcademicExperienceForm(
            current_context=self.current_context,
            data=self.request.POST or None,
            prefix='base_form',
            instance=educational_experience,
            start=start,
            end=end,
        )

        year_formset = AdmissionCurriculumEducationalExperienceYearFormSet(
            self.request.POST or None,
            initial=all_educational_experience_years,
            prefix='year_formset',
            form_kwargs={
                'current_year': current_academic_year.year,
                'prefix_index_start': int(
                    base_form.data.get(
                        base_form.add_prefix('end'),
                        base_form.initial['end'] if all_educational_experience_years else 0,
                    )
                ),
                'current_context': self.current_context,
            },
        )

        # We need to prevent the uploader component of osis-document from being initialized when the page is loaded
        # so that the events remain attached when the form is copied. The class identifying the component is replaced
        # in the default form and will be reset in the duplicated form, allowing osis-document to detect the file
        # fields in this new form, and set up the appropriate VueJS components.
        context_data["empty_form"] = loader.render_to_string(
            template_name='admission/forms/curriculum_experience_year_form.html',
            context={
                'year_form': year_formset.empty_form,
                'next_year': FOLLOWING_FORM_SET_PREFIX,
            },
        ).replace(OSIS_DOCUMENT_UPLOADER_CLASS, OSIS_DOCUMENT_UPLOADER_CLASS_PREFIX)

        context_data['current_year'] = current_academic_year.year
        context_data['form'] = base_form  # Trick template to display form tag
        context_data['base_form'] = base_form
        context_data['year_formset'] = year_formset
        context_data['linguistic_regimes_without_translation'] = list(REGIMES_LINGUISTIQUES_SANS_TRADUCTION)
        context_data['BE_ISO_CODE'] = BE_ISO_CODE
        context_data['FIRST_YEAR_WITH_ECTS_BE'] = VerifierCurriculum.PREMIERE_ANNEE_AVEC_CREDITS_ECTS_BE
        context_data['FORM_SET_PREFIX'] = FORM_SET_PREFIX
        context_data['FOLLOWING_FORM_SET_PREFIX'] = FOLLOWING_FORM_SET_PREFIX
        context_data['OSIS_DOCUMENT_UPLOADER_CLASS'] = OSIS_DOCUMENT_UPLOADER_CLASS
        context_data['OSIS_DOCUMENT_UPLOADER_CLASS_PREFIX'] = OSIS_DOCUMENT_UPLOADER_CLASS_PREFIX
        context_data['educational_experience'] = educational_experience
        context_data['existing_experience'] = self.existing_experience
        return context_data

    def post(self, request, *args, **kwargs):
        context_data = self.get_context_data(**kwargs)

        experience = context_data['educational_experience']

        base_form = context_data['base_form']
        year_formset = context_data['year_formset']

        # Check the forms
        if not self.check_forms(base_form, year_formset):
            messages.error(self.request, _("Please correct the errors below"))
            return self.render_to_response(context_data)

        enrolled_years = [
            year_form.cleaned_data['academic_year']
            for year_form in year_formset
            if year_form.cleaned_data['is_enrolled']
        ]

        enrolled_academic_years = {year.year: year for year in AcademicYear.objects.filter(year__in=enrolled_years)}

        # Clean not model fields
        for field in [
            'other_institute',
            'other_program',
            'start',
            'end',
        ]:
            base_form.cleaned_data.pop(field)

        if self.experience_id:
            # On update

            with transaction.atomic():
                # Save the base data
                educational_experience = self.educational_experience

                for field, field_value in base_form.cleaned_data.items():
                    setattr(experience, field, field_value)

                experience.save()

                # Save the enrolled years data
                for year_form in year_formset:
                    cleaned_data = year_form.cleaned_data
                    if cleaned_data.pop('is_enrolled'):
                        EducationalExperienceYear.objects.update_or_create(
                            educational_experience=educational_experience,
                            academic_year=enrolled_academic_years[cleaned_data.pop('academic_year')],
                            defaults=cleaned_data,
                        )

                # Remove the data related to the not enrolled years
                EducationalExperienceYear.objects.filter(educational_experience=educational_experience).exclude(
                    academic_year__year__in=enrolled_years,
                ).delete()

        else:
            # On creation

            # Save the base data
            with transaction.atomic():
                instance = EducationalExperience.objects.create(
                    person=self.admission.candidate,
                    **base_form.cleaned_data,
                )

                # Save the enrolled years data
                for year_form in year_formset:
                    cleaned_data = year_form.cleaned_data
                    if cleaned_data.pop('is_enrolled'):
                        cleaned_data['educational_experience'] = instance
                        cleaned_data['academic_year'] = enrolled_academic_years[cleaned_data['academic_year']]
                        EducationalExperienceYear.objects.create(**cleaned_data)

                self._experience_id = instance.uuid

                # Consider the experience as valuated
                AdmissionEducationalValuatedExperiences.objects.create(
                    baseadmission_id=self.admission.uuid,
                    educationalexperience_id=instance.uuid,
                )

                # Add the experience to the checklist
                if 'current' in self.admission.checklist:
                    admission = self.admission
                    experience_checklist = Checklist.initialiser_checklist_experience(instance.uuid).to_dict()
                    admission.checklist['current']['parcours_anterieur']['enfants'].append(experience_checklist)
                    admission.save(update_fields=['checklist'])

        return self.form_valid(base_form)

    def get_success_url(self):
        return reverse(
            self.base_namespace + ':update:curriculum:educational',
            kwargs={
                'uuid': self.admission_uuid,
                'experience_uuid': self.experience_id,
            },
        )

    def check_forms(self, base_form, year_formset):
        # Individual form check
        base_form.is_valid()
        year_formset.is_valid()

        country = base_form.cleaned_data.get('country')
        last_enrolled_year = base_form.cleaned_data.get('end')
        be_country = country and country.iso_code == BE_ISO_CODE
        linguistic_regime = base_form.cleaned_data.get('linguistic_regime')
        credits_are_required = (
            base_form.cleaned_data.get('evaluation_type') in VerifierCurriculum.SYSTEMES_EVALUATION_AVEC_CREDITS
        )
        transcript_is_required = base_form.cleaned_data.get('transcript_type') == TranscriptType.ONE_A_YEAR.name
        transcript_translation_is_required = (
            transcript_is_required
            and country
            and not be_country
            and linguistic_regime
            and linguistic_regime.code not in REGIMES_LINGUISTIQUES_SANS_TRADUCTION
        )
        has_enrolled_year = False
        obtained_diploma = base_form.cleaned_data.get('obtained_diploma')
        program_cycle = (
            base_form.cleaned_data['program'].cycle
            if base_form.cleaned_data.get('program')
            else base_form.cleaned_data['fwb_equivalent_program'].cycle
            if base_form.cleaned_data.get('fwb_equivalent_program')
            else ''
        )
        institute_community = base_form.cleaned_data.get('institute') and base_form.cleaned_data['institute'].community

        is_fwb_bachelor = (
            program_cycle == Cycle.FIRST_CYCLE.name
            and not obtained_diploma
            and institute_community == CommunityEnum.FRENCH_SPEAKING.name
        )

        is_fwb_master = (
            program_cycle == Cycle.SECOND_CYCLE.name
            and not obtained_diploma
            and institute_community == CommunityEnum.FRENCH_SPEAKING.name
        )

        # Cross-form check
        for form in year_formset:
            if form.cleaned_data.get('is_enrolled'):
                has_enrolled_year = True
                self.clean_experience_year_form(
                    be_country,
                    credits_are_required,
                    form,
                    transcript_is_required,
                    transcript_translation_is_required,
                    is_fwb_bachelor,
                    is_fwb_master,
                )

        if not has_enrolled_year:
            base_form.add_error(None, _('At least one academic year is required.'))

        if last_enrolled_year and be_country:
            # The evaluation system in Belgium depends on the years
            base_form.cleaned_data['evaluation_type'] = (
                EvaluationSystem.ECTS_CREDITS.name
                if int(last_enrolled_year.year) >= VerifierCurriculum.PREMIERE_ANNEE_AVEC_CREDITS_ECTS_BE
                else EvaluationSystem.NO_CREDIT_SYSTEM.name
            )

        return base_form.is_valid() and year_formset.is_valid()

    def clean_experience_year_form(
        self,
        be_country,
        credits_are_required,
        form,
        transcript_is_required,
        transcript_translation_is_required,
        is_fwb_bachelor,
        is_fwb_master,
    ):
        cleaned_data = form.cleaned_data

        # Credit fields
        if (
            cleaned_data.get('academic_year') >= VerifierCurriculum.PREMIERE_ANNEE_AVEC_CREDITS_ECTS_BE
            if be_country
            else credits_are_required
        ):

            acquired_credit_number = cleaned_data.get('acquired_credit_number', None)
            registered_credit_number = cleaned_data.get('registered_credit_number', None)
            credits_are_required_for_this_year = cleaned_data.get('result') != Result.WAITING_RESULT.name

            if acquired_credit_number is None or acquired_credit_number == '':
                if credits_are_required_for_this_year:
                    form.add_error('acquired_credit_number', FIELD_REQUIRED_MESSAGE)
            else:
                acquired_credit_number = Decimal(acquired_credit_number)
                if acquired_credit_number < MINIMUM_CREDIT_NUMBER:
                    form.add_error(
                        'acquired_credit_number',
                        _('This value must be equal to or greater than %(MINIMUM_CREDIT_NUMBER)s')
                        % {'MINIMUM_CREDIT_NUMBER': MINIMUM_CREDIT_NUMBER},
                    )

            if registered_credit_number is None or registered_credit_number == '':
                if credits_are_required_for_this_year:
                    form.add_error('registered_credit_number', FIELD_REQUIRED_MESSAGE)
            else:
                registered_credit_number = Decimal(registered_credit_number)
                if registered_credit_number <= MINIMUM_CREDIT_NUMBER:
                    form.add_error(
                        'registered_credit_number',
                        _('This value must be greater than %(MINIMUM_CREDIT_NUMBER)s')
                        % {'MINIMUM_CREDIT_NUMBER': MINIMUM_CREDIT_NUMBER},
                    )

            if isinstance(acquired_credit_number, Decimal) and isinstance(registered_credit_number, Decimal):
                if acquired_credit_number > registered_credit_number:
                    form.add_error(
                        'acquired_credit_number',
                        _('This value may not exceed the number of registered credits'),
                    )

        else:
            cleaned_data['acquired_credit_number'] = None
            cleaned_data['registered_credit_number'] = None

        # Transcript fields
        if not transcript_is_required:
            cleaned_data['transcript'] = []
        if not transcript_translation_is_required:
            cleaned_data['transcript_translation'] = []

        # FWB fields
        if not is_fwb_bachelor:
            cleaned_data['with_block_1'] = None
            cleaned_data['is_102_change_of_course'] = None

        if not is_fwb_master:
            cleaned_data['with_complement'] = None

        if not cleaned_data['with_block_1'] and not cleaned_data['with_complement']:
            cleaned_data['fwb_registered_credit_number'] = None
            cleaned_data['fwb_acquired_credit_number'] = None

    def get_educational_experience_year_set_with_lost_years(self, educational_experience_year_set):
        """
        Get a list of all the years of the experience, even the ones that have not been filled
        :param educational_experience_year_set: The list of enrolled years
        :return: a dict containing the start and the end years, and all years between them
        """
        educational_experience_year_set_with_lost_years = []
        start = None
        end = None

        if educational_experience_year_set:
            start = educational_experience_year_set[len(educational_experience_year_set) - 1]['year']
            end = educational_experience_year_set[0]['year']

            taken_years = {}

            for experience in educational_experience_year_set:
                experience['academic_year'] = experience.pop('year')
                taken_years[experience['academic_year']] = experience

            educational_experience_year_set_with_lost_years = [
                taken_years.get(
                    year,
                    {
                        'academic_year': year,
                        'is_enrolled': False,
                    },
                )
                for year in range(end, start - 1, -1)
            ]

        return {
            'start': start,
            'end': end,
            'educational_experience_year_set_with_lost_years': educational_experience_year_set_with_lost_years,
        }


class CurriculumNonEducationalExperienceFormView(AdmissionFormMixin, LoadDossierViewMixin, FormView):
    urlpatterns = {
        'non_educational': 'non_educational/<uuid:experience_uuid>',
        'non_educational_create': 'non_educational/create',
    }
    template_name = 'admission/forms/curriculum_non_educational_experience.html'
    permission_required = 'admission.change_admission_curriculum'
    form_class = AdmissionCurriculumProfessionalExperienceForm
    extra_context = {
        'without_menu': True,
    }
    update_requested_documents = True
    update_admission_author = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.existing_experience = False
        self._experience_id = None

    @property
    def experience_id(self):
        return self._experience_id or self.kwargs.get('experience_uuid', None)

    @cached_property
    def non_educational_experience(self) -> EducationalExperience:
        if self.experience_id:
            try:
                experience = ProfessionalExperience.objects.get(
                    uuid=self.experience_id,
                    person=self.admission.candidate,
                )
                self.existing_experience = True
                return experience
            except ProfessionalExperience.DoesNotExist:
                messages.error(self.request, _('Non-educational experience not found.'))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.non_educational_experience
        kwargs['is_continuing'] = self.is_continuing
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['CURRICULUM_ACTIVITY_LABEL'] = CURRICULUM_ACTIVITY_LABEL
        context['existing_experience'] = self.existing_experience
        return context

    def form_valid(self, form):
        cleaned_data = form.cleaned_data

        # The start date is the first day of the specified month
        cleaned_data['start_date'] = datetime.date(
            int(cleaned_data.pop('start_date_year')),
            int(cleaned_data.pop('start_date_month')),
            1,
        )
        # The end date is the last day of the specified month
        end_date_year = int(cleaned_data.pop('end_date_year'))
        end_date_month = int(cleaned_data.pop('end_date_month'))
        cleaned_data['end_date'] = datetime.date(
            end_date_year,
            end_date_month,
            calendar.monthrange(end_date_year, end_date_month)[1],
        )

        if self.existing_experience:
            # On update
            experience = self.non_educational_experience

            for field, field_value in cleaned_data.items():
                setattr(experience, field, field_value)

            experience.save()

        else:
            # On create
            with transaction.atomic():
                instance = ProfessionalExperience.objects.create(
                    person=self.admission.candidate,
                    **cleaned_data,
                )

                self._experience_id = instance.uuid

                # Consider the experience as valuated
                AdmissionProfessionalValuatedExperiences.objects.create(
                    baseadmission_id=self.admission.uuid,
                    professionalexperience_id=instance.uuid,
                )

                # Add the experience to the checklist
                if 'current' in self.admission.checklist:
                    admission = self.admission
                    experience_checklist = Checklist.initialiser_checklist_experience(instance.uuid).to_dict()
                    admission.checklist['current']['parcours_anterieur']['enfants'].append(experience_checklist)
                    admission.save(update_fields=['checklist'])

        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            self.base_namespace + ':update:curriculum:non_educational',
            kwargs={
                'uuid': self.admission_uuid,
                'experience_uuid': self.experience_id,
            },
        )


class CurriculumBaseDeleteView(LoadDossierViewMixin, DeleteView):
    permission_required = 'admission.change_admission_curriculum'
    slug_field = 'uuid'
    slug_url_kwarg = 'experience_uuid'
    template_name = 'admission/empty_template.html'

    @property
    def experience_id(self):
        return self.kwargs.get('experience_uuid', None)

    def delete(self, request, *args, **kwargs):
        # Delete the experience
        try:
            delete = super().delete(request, *args, **kwargs)
        except ProtectedError as e:
            free_approval_condition = next(
                (obj for obj in e.protected_objects if isinstance(obj, FreeAdditionalApprovalCondition)),
                None,
            )
            error_message = (
                _(
                    'Cannot delete the experience because it is used as additional condition for the '
                    'proposition {admission}.'.format(admission=free_approval_condition.admission)
                )
                if free_approval_condition
                else _('Cannot delete the experience because it is used in another context.')
            )
            messages.error(self.request, error_message)
            return redirect(self.get_failure_url())

        # Delete the information of the experience from the checklist
        admission: BaseAdmission = self.admission

        if 'current' in admission.checklist:
            experiences = admission.checklist['current']['parcours_anterieur']['enfants']

            experience_uuid = str(self.kwargs.get('experience_uuid'))

            for index, experience in enumerate(experiences):
                if experience.get('extra', {}).get('identifiant') == experience_uuid:
                    experiences.pop(index)
                    break

        admission.last_update_author = self.request.user.person

        admission.save()

        self.admission.update_requested_documents()

        return delete

    def get_success_url(self):
        success_url = reverse(self.base_namespace + ':checklist', kwargs={'uuid': self.admission_uuid})

        redirect_to = self.request.POST.get('redirect_to')
        if redirect_to:
            success_url += redirect_to

        return success_url

    def get_failure_url(self):
        raise NotImplemented


class CurriculumEducationalExperienceDeleteView(CurriculumBaseDeleteView):
    urlpatterns = {'educational_delete': 'educational/<uuid:experience_uuid>/delete'}

    def get_queryset(self):
        return EducationalExperience.objects.filter(person=self.admission.candidate)

    def get_failure_url(self):
        return reverse(
            self.base_namespace + ':update:curriculum:educational',
            kwargs={
                'uuid': self.admission_uuid,
                'experience_uuid': self.experience_id,
            },
        )


class CurriculumNonEducationalExperienceDeleteView(CurriculumBaseDeleteView):
    urlpatterns = {'non_educational_delete': 'non_educational/<uuid:experience_uuid>/delete'}

    def get_queryset(self):
        return ProfessionalExperience.objects.filter(person=self.admission.candidate)

    def get_failure_url(self):
        return reverse(
            self.base_namespace + ':update:curriculum:non_educational',
            kwargs={
                'uuid': self.admission_uuid,
                'experience_uuid': self.experience_id,
            },
        )


class CurriculumBaseExperienceDuplicateView(AdmissionFormMixin, LoadDossierViewMixin, FormView):
    """
    View to duplicate a curriculum experience.
    """

    permission_required = 'admission.change_admission_curriculum'
    slug_field = 'uuid'
    slug_url_kwarg = 'experience_uuid'
    template_name = 'admission/empty_template.html'
    form_class = forms.Form
    update_admission_author = True
    update_requested_documents = True

    experience_model = None  # Name of the model of the experience to duplicate
    valuated_experience_model = None  # Name of the model of the valuated experience
    valuated_experience_field_id_name = None  # Name of the field of the experience in the valuated experience model

    @property
    def experience_id(self):
        return self.kwargs.get('experience_uuid', None)

    def additional_duplications(self, duplicated_experience):
        """
        Create additional objects that must be duplicated in addition to the duplicated experience.
        :param duplicated_experience: The duplicated experience.
        :return: The list of additional objects.
        """
        return []

    def additional_duplications_save(self, duplicated_objects):
        """
        Save additional objects that must be duplicated in addition to the duplicated experience.
        :param duplicated_objects: The list of additional objects returned by the 'additional_duplications' method.
        """
        pass

    def form_valid(self, form):
        # Retrieve the experience to duplicate
        duplicated_experience = get_object_or_404(
            self.experience_model.objects.select_related('person'),
            uuid=self.experience_id,
        )

        # Retrieve the valuations of the experience to duplicate
        valuated_admissions: QuerySet[
            Union[AdmissionProfessionalValuatedExperiences, AdmissionEducationalValuatedExperiences]
        ] = self.valuated_experience_model.objects.filter(
            **{self.valuated_experience_field_id_name: self.experience_id}
        ).select_related(
            'baseadmission'
        )

        # Initialize the new experience
        duplicated_experience.pk = None
        duplicated_experience.external_id = None
        duplicated_experience.uuid = uuid.uuid4()
        duplicated_experience._state_adding = True

        # Initialize the sub models if necessary
        additional_duplications = self.additional_duplications(duplicated_experience=duplicated_experience)

        all_duplications = [duplicated_experience]

        if additional_duplications:
            all_duplications += additional_duplications

        # Make a copy of all documents and affect them to the new experience and to the sub models, if any
        copy_documents(all_duplications)

        # Save the new experience
        duplicated_experience.save()

        # Save the sub models, if any
        self.additional_duplications_save(additional_duplications)

        initial_checklist = Checklist.initialiser_checklist_experience(duplicated_experience.uuid).to_dict()

        new_valuations = []
        admissions_to_update = []

        # Loop over the valuated admissions by the experience
        for current_valuation in valuated_admissions:

            # Initialize the valuation of the admission by the new experience
            new_valuations.append(
                self.valuated_experience_model(
                    **{
                        'baseadmission_id': current_valuation.baseadmission_id,
                        self.valuated_experience_field_id_name: duplicated_experience.uuid,
                    },
                )
            )

            # Initialize the checklist of the duplicated experience
            admission_experience_checklists = (
                current_valuation.baseadmission.checklist.get('current', {})
                .get('parcours_anterieur', {})
                .get('enfants')
            )
            if admission_experience_checklists is not None:
                admission_experience_checklists.append(initial_checklist)
                admissions_to_update.append(current_valuation.baseadmission)

        if new_valuations:
            self.valuated_experience_model.objects.bulk_create(new_valuations)

        if admissions_to_update:
            BaseAdmission.objects.bulk_update(admissions_to_update, ['checklist'])

        return super().form_valid(form)

    def get_success_url(self):
        success_url = reverse(self.base_namespace + ':checklist', kwargs={'uuid': self.admission_uuid})

        redirect_to = self.request.POST.get('redirect_to')
        if redirect_to:
            success_url += redirect_to

        return success_url


class CurriculumNonEducationalExperienceDuplicateView(CurriculumBaseExperienceDuplicateView):
    """
    View to duplicate a professional experience.
    """

    urlpatterns = {'non_educational_duplicate': 'non_educational/<uuid:experience_uuid>/duplicate'}
    experience_model = ProfessionalExperience
    valuated_experience_model = AdmissionProfessionalValuatedExperiences
    valuated_experience_field_id_name = 'professionalexperience_id'


class CurriculumEducationalExperienceDuplicateView(CurriculumBaseExperienceDuplicateView):
    """
    View to duplicate an educational experience.
    """

    urlpatterns = {'educational_duplicate': 'educational/<uuid:experience_uuid>/duplicate'}
    experience_model = EducationalExperience
    valuated_experience_model = AdmissionEducationalValuatedExperiences
    valuated_experience_field_id_name = 'educationalexperience_id'

    def additional_duplications(self, duplicated_experience):
        experience_years = EducationalExperienceYear.objects.filter(
            educational_experience__uuid=self.experience_id
        ).select_related('educational_experience__person')

        for duplicated_experience_year in experience_years:
            duplicated_experience_year.pk = None
            duplicated_experience_year.external_id = None
            duplicated_experience_year._state_adding = True
            duplicated_experience_year.uuid = uuid.uuid4()
            duplicated_experience_year.educational_experience = duplicated_experience

        return experience_years

    def additional_duplications_save(self, duplicated_objects):
        EducationalExperienceYear.objects.bulk_create(duplicated_objects)
