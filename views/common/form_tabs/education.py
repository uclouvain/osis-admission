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
from typing import List
from uuid import UUID

from django.urls import reverse
from django.utils.functional import cached_property

from admission.contrib.models import EPCInjection as AdmissionEPCInjection
from admission.contrib.models.epc_injection import EPCInjectionType, EPCInjectionStatus as AdmissionEPCInjectionStatus
from admission.ddd.admission.enums import Onglets
from admission.forms.admission.education import AdmissionBachelorEducationForeignDiplomaForm
from admission.infrastructure.admission.domain.service.profil_candidat import ProfilCandidatTranslator
from admission.views.common.mixins import LoadDossierViewMixin, AdmissionFormMixin
from base.models.enums.education_group_types import TrainingType
from osis_profile.models.epc_injection import (
    EPCInjection as CurriculumEPCInjection,
    ExperienceType,
    EPCInjectionStatus as CurriculumEPCInjectionStatus,
)
from osis_profile.views.edit_etudes_secondaires import EditEtudesSecondairesView

__all__ = [
    'AdmissionEducationFormView',
]


class AdmissionEducationFormView(AdmissionFormMixin, LoadDossierViewMixin, EditEtudesSecondairesView):
    urlpatterns = 'education'
    template_name = 'admission/forms/education.html'
    specific_questions_tab = Onglets.ETUDES_SECONDAIRES
    update_admission_author = True
    permission_required = 'admission.change_admission_secondary_studies'
    foreign_form_class = AdmissionBachelorEducationForeignDiplomaForm
    extra_context = {'force_form': True}

    def has_permission(self):
        return super().has_permission() and self.can_be_updated

    def traitement_specifique(self, experience_uuid: UUID, experiences_supprimees: List[UUID] = None):
        pass

    @cached_property
    def is_bachelor(self):
        return self.proposition.formation.type == TrainingType.BACHELOR.name

    @cached_property
    def person(self):
        return self.admission.candidate

    @cached_property
    def high_school_diploma(self):
        return {
            **super().high_school_diploma,
            'specific_question_answers': self.admission.specific_question_answers,
            'is_vae_potential': ProfilCandidatTranslator.est_potentiel_vae(self.person.global_id),
        }

    @cached_property
    def diploma(self):
        return next(
            (
                self.high_school_diploma[diploma]
                for diploma in ['belgian_diploma', 'foreign_diploma', 'high_school_diploma_alternative']
            ),
            None,
        )

    def get_template_names(self):
        if self.is_bachelor:
            return ['admission/forms/bachelor_education.html']
        return ['admission/forms/education.html']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['form_item_configurations'] = self.specific_questions
        return kwargs

    @cached_property
    def is_med_dent_training(self):
        return self.proposition.formation.est_formation_medecine_ou_dentisterie

    def get_success_url(self):
        return (
            self.next_url or self.request.get_full_path()
            if self.is_general
            else reverse(f'{self.base_namespace}:education', kwargs=self.kwargs)
        )

    def update_current_admission_on_form_valid(self, form, admission):
        admission.specific_question_answers = form.cleaned_data['specific_question_answers'] or {}

    @property
    def can_be_updated(self):
        admission_injections = AdmissionEPCInjection.objects.filter(
            admission__candidate_id=self.person.pk,
            type=EPCInjectionType.DEMANDE.name,
            status__in=AdmissionEPCInjectionStatus.blocking_statuses_for_experience(),
        )
        cv_injections = CurriculumEPCInjection.objects.filter(
            person_id=self.person.pk,
            type_experience=ExperienceType.HIGH_SCHOOL.name,
            status__in=CurriculumEPCInjectionStatus.blocking_statuses_for_experience(),
        )

        return not (
            (self.diploma and self.diploma.external_id) or cv_injections.exists() or admission_injections.exists()
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        if self.is_bachelor:
            context_data['is_vae_potential'] = self.high_school_diploma['is_vae_potential']
        return context_data
