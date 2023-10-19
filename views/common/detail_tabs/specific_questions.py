# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.functional import cached_property
from django.views.generic import TemplateView

from admission.calendar.admission_calendar import (
    AdmissionPoolExternalReorientationCalendar,
    AdmissionPoolExternalEnrollmentChangeCalendar,
)
from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.infrastructure.admission.domain.service.calendrier_inscription import CalendrierInscription
from admission.infrastructure.admission.domain.service.profil_candidat import ProfilCandidatTranslator
from admission.views.doctorate.mixins import LoadDossierViewMixin
from base.models.enums.education_group_types import TrainingType


__all__ = [
    'SpecificQuestionsDetailView',
]


class SpecificQuestionsMixinView(LoadDossierViewMixin):
    urlpatterns = 'specific-questions'
    specific_questions_tab = OngletsDemande.INFORMATIONS_ADDITIONNELLES

    @cached_property
    def identification_dto(self):
        return ProfilCandidatTranslator.get_identification(
            matricule=self.proposition.matricule_candidat,
        )

    @property
    def display_visa_question(self):
        return self.is_general and self.identification_dto.est_concerne_par_visa

    @property
    def display_pool_questions(self):
        return self.is_general and self.proposition.formation.type == TrainingType.BACHELOR.name

    @property
    def enrolled_for_contingent_training(self):
        return CalendrierInscription.inscrit_formation_contingentee(
            sigle=self.proposition.formation.sigle,
        )


class SpecificQuestionsDetailView(SpecificQuestionsMixinView, TemplateView):
    template_name = 'admission/details/specific_questions.html'
    permission_required = 'admission.view_admission_specific_questions'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['proposition'] = context['admission']

        if self.is_general:
            context['display_visa_question'] = self.display_visa_question

            context['enrolled_for_contingent_training'] = self.enrolled_for_contingent_training

            # Simulate the opening of the required pools (reorientation and modification)
            pools = [
                (AdmissionPoolExternalReorientationCalendar.event_reference, 0),
                (AdmissionPoolExternalEnrollmentChangeCalendar.event_reference, 0),
            ]

            context['eligible_for_reorientation'] = CalendrierInscription.eligible_a_la_reorientation(
                program=self.proposition.formation.type,
                sigle=self.proposition.formation.sigle,
                proposition=self.proposition,
                pool_ouverts=pools,
            )
            context['eligible_for_modification'] = CalendrierInscription.eligible_a_la_modification(
                program=self.proposition.formation.type,
                sigle=self.proposition.formation.sigle,
                proposition=self.proposition,
                pool_ouverts=pools,
            )

        return context
