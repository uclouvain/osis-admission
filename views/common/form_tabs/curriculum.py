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

from django.contrib import messages
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from admission.contrib.models.base import (
    AdmissionEducationalValuatedExperiences,
    AdmissionProfessionalValuatedExperiences,
)
from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.checklist import FreeAdditionalApprovalCondition
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.forms.specific_question import ConfigurableFormMixin
from admission.views.doctorate.mixins import AdmissionFormMixin, LoadDossierViewMixin
from osis_profile.views.delete_experience_academique import DeleteExperienceAcademiqueView
from osis_profile.views.delete_experience_non_academique import DeleteExperienceNonAcademiqueView
from osis_profile.views.edit_experience_academique import EditExperienceAcademiqueView
from osis_profile.views.edit_experience_non_academique import EditExperienceNonAcademiqueView
from osis_profile.views.parcours_externe_mixins import DeleteEducationalExperienceMixin

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

    @property
    def educational_experience_filter_uuid(self):
        return {'uuid': self.experience_id}

    def traitement_specifique_de_creation(self):
        # Consider the experience as valuated
        AdmissionEducationalValuatedExperiences.objects.create(
            baseadmission_id=self.admission.uuid,
            educationalexperience_id=self._experience_id,
        )
        # Add the experience to the checklist
        if 'current' in self.admission.checklist:
            admission = self.admission
            experience_checklist = Checklist.initialiser_checklist_experience(self._experience_id).to_dict()
            admission.checklist['current']['parcours_anterieur']['enfants'].append(experience_checklist)
            admission.save(update_fields=['checklist'])

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

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'prevent_quitting_template': 'admission/includes/prevent_quitting_button.html',
        }


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

    @property
    def person(self):
        return self.admission.candidate

    def traitement_specifique_de_creation(self):
        # Consider the experience as valuated
        AdmissionProfessionalValuatedExperiences.objects.create(
            baseadmission_id=self.admission.uuid,
            professionalexperience_id=self._experience_id,
        )
        # Add the experience to the checklist
        if 'current' in self.admission.checklist:
            admission = self.admission
            experience_checklist = Checklist.initialiser_checklist_experience(self._experience_id).to_dict()
            admission.checklist['current']['parcours_anterieur']['enfants'].append(experience_checklist)
            admission.save(update_fields=['checklist'])

    def get_success_url(self):
        return reverse(
            self.base_namespace + ':update:curriculum:non_educational',
            kwargs={
                'uuid': self.admission_uuid,
                'experience_uuid': self.experience_id,
            },
        )

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'prevent_quitting_template': 'admission/includes/prevent_quitting_button.html',
        }


class CurriculumBaseDeleteView(LoadDossierViewMixin, DeleteEducationalExperienceMixin):
    permission_required = 'admission.change_admission_curriculum'

    @property
    def person(self):
        return self.admission.candidate

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


class CurriculumEducationalExperienceDeleteView(CurriculumBaseDeleteView, DeleteExperienceAcademiqueView):
    urlpatterns = {'educational_delete': 'educational/<uuid:experience_uuid>/delete'}

    def get_failure_url(self):
        return reverse(
            self.base_namespace + ':update:curriculum:educational',
            kwargs={
                'uuid': self.admission_uuid,
                'experience_uuid': self.experience_id,
            },
        )


class CurriculumNonEducationalExperienceDeleteView(CurriculumBaseDeleteView, DeleteExperienceNonAcademiqueView):
    urlpatterns = {'non_educational_delete': 'non_educational/<uuid:experience_uuid>/delete'}

    def get_failure_url(self):
        return reverse(
            self.base_namespace + ':update:curriculum:non_educational',
            kwargs={
                'uuid': self.admission_uuid,
                'experience_uuid': self.experience_id,
            },
        )
