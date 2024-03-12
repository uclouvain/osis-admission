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

from django.contrib import messages
from django.db import transaction
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView, FormView

from admission.contrib.models.base import (
    AdmissionEducationalValuatedExperiences,
    BaseAdmission,
    AdmissionProfessionalValuatedExperiences,
)
from admission.contrib.models.checklist import FreeAdditionalApprovalCondition
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.forms.specific_question import ConfigurableFormMixin
from admission.views.doctorate.mixins import AdmissionFormMixin, LoadDossierViewMixin
from base.models.academic_year import AcademicYear
from osis_profile.models import EducationalExperience, EducationalExperienceYear, ProfessionalExperience
from osis_profile.views.edit_experience_academique import EditExperienceAcademiqueView
from osis_profile.views.edit_experience_non_academique import EditExperienceNonAcademiqueView

__all__ = [
    'CurriculumEducationalExperienceFormView',
    'CurriculumEducationalExperienceDeleteView',
    'CurriculumGlobalFormView',
    'CurriculumNonEducationalExperienceFormView',
    'CurriculumNonEducationalExperienceDeleteView',
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


class CurriculumEducationalExperienceFormView(AdmissionFormMixin, LoadDossierViewMixin, EditExperienceAcademiqueView):
    urlpatterns = {
        'educational': 'educational/<uuid:experience_uuid>',
        'educational_create': 'educational/create',
    }
    template_name = 'admission/forms/curriculum_educational_experience.html'
    permission_required = 'admission.change_admission_curriculum'
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

    def post(self, request, *args, **kwargs):
        if self.experience_id:
            # On update
            return super().post(request, *args, **kwargs)

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

        academic_years = {year.year: year for year in AcademicYear.objects.filter(year__in=enrolled_years)}

        # Clean not model fields
        for field in [
            'other_institute',
            'other_program',
            'start',
            'end',
        ]:
            base_form.cleaned_data.pop(field)

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
                cleaned_data['educational_experience'] = instance
                cleaned_data['academic_year'] = academic_years[cleaned_data['academic_year']]
                if cleaned_data.pop('is_enrolled'):
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

    @property
    def person(self):
        return self.admission.candidate

    def get_success_url(self):
        return reverse(
            self.base_namespace + ':update:curriculum:educational',
            kwargs={
                'uuid': self.admission_uuid,
                'experience_uuid': self.experience_id,
            },
        )


class CurriculumNonEducationalExperienceFormView(
    AdmissionFormMixin,
    LoadDossierViewMixin,
    EditExperienceNonAcademiqueView
):
    urlpatterns = {
        'non_educational': 'non_educational/<uuid:experience_uuid>',
        'non_educational_create': 'non_educational/create',
    }
    template_name = 'admission/forms/curriculum_non_educational_experience.html'
    permission_required = 'admission.change_admission_curriculum'
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

    @property
    def person(self):
        return self.admission.candidate

    def form_valid(self, form):
        if self.existing_experience:
            # On update
            return super().form_valid(form)

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
        return reverse(self.base_namespace + ':checklist', kwargs={'uuid': self.admission_uuid}) + '#parcours_anterieur'

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
