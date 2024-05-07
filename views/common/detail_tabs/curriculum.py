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
from django.http import Http404
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from admission.ddd.admission.commands import (
    RecupererExperienceAcademiqueQuery,
    RecupererExperienceNonAcademiqueQuery,
)
from admission.ddd.admission.domain.validator.exceptions import ExperienceNonTrouveeException
from admission.utils import get_experience_urls
from admission.views.common.mixins import LoadDossierViewMixin
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceNonAcademiqueDTO, ExperienceAcademiqueDTO
from infrastructure.messages_bus import message_bus_instance
from osis_profile import BE_ISO_CODE, REGIMES_LINGUISTIQUES_SANS_TRADUCTION
from osis_profile.models.enums.curriculum import CURRICULUM_ACTIVITY_LABEL
from osis_profile.views.edit_experience_academique import SYSTEMES_EVALUATION_AVEC_CREDITS

__all__ = [
    'CurriculumEducationalExperienceDetailView',
    'CurriculumNonEducationalExperienceDetailView',
]


class CurriculumEducationalExperienceDetailView(LoadDossierViewMixin, TemplateView):
    urlpatterns = {
        'educational': 'educational/<uuid:experience_uuid>',
    }
    permission_required = 'admission.view_admission_curriculum'
    template_name = 'admission/details/curriculum_educational_experience.html'

    @property
    def experience_uuid(self) -> str:
        return self.kwargs.get('experience_uuid', '')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            experience: ExperienceAcademiqueDTO = message_bus_instance.invoke(
                RecupererExperienceAcademiqueQuery(
                    global_id=self.proposition.matricule_candidat,
                    uuid_proposition=self.proposition.uuid,
                    uuid_experience=self.experience_uuid,
                )
            )
        except ExperienceNonTrouveeException as exception:
            raise Http404(exception.message)

        context['experience'] = experience
        context['is_foreign_experience'] = experience.pays != BE_ISO_CODE
        context['is_belgian_experience'] = experience.pays == BE_ISO_CODE
        context['translation_required'] = (
            (self.is_general or self.is_doctorate)
            and experience.regime_linguistique
            and experience.regime_linguistique not in REGIMES_LINGUISTIQUES_SANS_TRADUCTION
        )
        context['evaluation_system_with_credits'] = experience.systeme_evaluation in SYSTEMES_EVALUATION_AVEC_CREDITS
        context['title'] = _('Academic course')

        experience_urls = get_experience_urls(
            user=self.request.user,
            admission=self.admission,
            experience=experience,
            candidate_noma=self.proposition.noma_candidat,
        )

        context['edit_url'] = experience_urls['edit_url']
        context['edit_new_link_tab'] = experience_urls['edit_new_link_tab']

        return context


class CurriculumNonEducationalExperienceDetailView(LoadDossierViewMixin, TemplateView):
    permission_required = 'admission.view_admission_curriculum'
    urlpatterns = {
        'non_educational': 'non_educational/<uuid:experience_uuid>',
    }
    template_name = 'admission/details/curriculum_non_educational_experience.html'

    @property
    def experience_uuid(self) -> str:
        return self.kwargs.get('experience_uuid', '')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            experience: ExperienceNonAcademiqueDTO = message_bus_instance.invoke(
                RecupererExperienceNonAcademiqueQuery(
                    global_id=self.proposition.matricule_candidat,
                    uuid_proposition=self.proposition.uuid,
                    uuid_experience=self.experience_uuid,
                )
            )
        except ExperienceNonTrouveeException as exception:
            raise Http404(exception.message)

        context['experience'] = experience
        context['CURRICULUM_ACTIVITY_LABEL'] = CURRICULUM_ACTIVITY_LABEL
        context['title'] = _('Non-academic activity')

        experience_urls = get_experience_urls(
            user=self.request.user,
            admission=self.admission,
            experience=experience,
            candidate_noma=self.proposition.noma_candidat,
        )

        context['edit_url'] = experience_urls['edit_url']
        context['edit_new_link_tab'] = experience_urls['edit_new_link_tab']

        return context
