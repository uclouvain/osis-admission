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
import json

from django.views.generic import TemplateView
from osis_comment.contrib.mixins import CommentEntryAPIMixin
from osis_comment.models import CommentEntry

from admission.auth.roles.admission_reader import AdmissionReader
from admission.auth.roles.central_manager import CentralManager
from admission.auth.roles.program_manager import ProgramManager as ProgramManagerAdmission
from admission.auth.roles.sic_management import SicManagement
from admission.ddd.admission.commands import RechercherParcoursAnterieurQuery, RecupererEtudesSecondairesQuery
from admission.ddd.admission.doctorat.preparation.domain.model.enums import OngletsChecklist as DoctoratOngletsChecklist
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import CurriculumAdmissionDTO
from admission.ddd.admission.enums.valorisation_experience import ExperiencesCVRecuperees
from admission.ddd.admission.formation_continue.domain.model.enums import OngletsChecklist as ContinueOngletsChecklist
from admission.ddd.admission.formation_generale.domain.model.enums import OngletsChecklist as GeneralOngletsChecklist
from admission.views.common.mixins import LoadDossierViewMixin
from backoffice.settings.base import CKEDITOR_CONFIGS
from base.auth.roles.program_manager import ProgramManager
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.permissions import _get_roles_assigned_to_user

__all__ = [
    "AdmissionCommentsView",
    "AdmissionCommentApiView",
    "COMMENT_TAG_SIC",
    "COMMENT_TAG_FAC",
    "COMMENT_TAG_GLOBAL",
    "COMMENT_TAG_IUFC_FOR_FAC",
    "COMMENT_TAG_FAC_FOR_IUFC",
]
__namespace__ = False

COMMENT_TAG_SIC = 'SIC'
COMMENT_TAG_FAC = 'FAC'
COMMENT_TAG_IUFC_FOR_FAC = 'IUFC_for_FAC'
COMMENT_TAG_FAC_FOR_IUFC = 'FAC_for_IUFC'
COMMENT_TAG_GLOBAL = 'GLOBAL'
CHECKLIST_TABS_WITH_SIC_AND_FAC_COMMENTS = {
    'decision_facultaire',
}


class AdmissionCommentsView(LoadDossierViewMixin, TemplateView):
    urlpatterns = 'comments'
    permission_required = 'admission.view_enrolment_application'
    template_name = "admission/details/comments.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['ckeditor_config'] = json.dumps(CKEDITOR_CONFIGS['minimal'])

        context['COMMENT_TAG_FAC'] = f'{COMMENT_TAG_FAC},{COMMENT_TAG_GLOBAL}'
        context['COMMENT_TAG_SIC'] = f'{COMMENT_TAG_SIC},{COMMENT_TAG_GLOBAL}'

        if self.is_general or self.is_doctorate:
            context['CHECKLIST_TABS_WITH_SIC_AND_FAC_COMMENTS'] = CHECKLIST_TABS_WITH_SIC_AND_FAC_COMMENTS

            context['checklist_tags'] = (
                DoctoratOngletsChecklist.choices_except(DoctoratOngletsChecklist.experiences_parcours_anterieur)
                if self.is_doctorate
                else GeneralOngletsChecklist.choices_except(GeneralOngletsChecklist.experiences_parcours_anterieur)
            )

            # Get the names of every experience
            curriculum: CurriculumAdmissionDTO = message_bus_instance.invoke(
                RechercherParcoursAnterieurQuery(
                    global_id=self.proposition.matricule_candidat,
                    uuid_proposition=self.proposition.uuid,
                    experiences_cv_recuperees=ExperiencesCVRecuperees.TOUTES
                    if self.proposition.est_non_soumise
                    else ExperiencesCVRecuperees.SEULEMENT_VALORISEES_PAR_ADMISSION,
                )
            )

            experiences_names_by_uuid = {}

            for experience in curriculum.experiences_academiques:
                experiences_names_by_uuid[experience.uuid] = experience.titre_formate

            for experience in curriculum.experiences_non_academiques:
                experiences_names_by_uuid[experience.uuid] = experience.titre_formate

            if self.is_general:
                secondary_studies = message_bus_instance.invoke(
                    RecupererEtudesSecondairesQuery(matricule_candidat=self.proposition.matricule_candidat)
                )
                if secondary_studies:
                    experiences_names_by_uuid[secondary_studies.uuid] = secondary_studies.titre_formate

            context['experiences_names_by_uuid'] = experiences_names_by_uuid

        elif self.is_continuing:
            context['checklist_tags'] = ContinueOngletsChecklist.choices()

        return context


class AdmissionCommentApiView(CommentEntryAPIMixin):
    urlpatterns = {
        'sic-comments': [f"sic-comments", f"sic-comments/<uuid:comment_uuid>"],
        'fac-comments': [f"fac-comments", f"fac-comments/<uuid:comment_uuid>"],
        'other-comments': [f"other-comments", f"other-comments/<uuid:comment_uuid>"],
    }
    roles = {
        'sic-comments': {SicManagement, CentralManager},
        'fac-comments': {ProgramManagerAdmission, AdmissionReader, ProgramManager},
    }

    def dispatch(self, request, *args, **kwargs):
        self.relevant_roles = _get_roles_assigned_to_user(self.request.user)
        self.url_name = self.request.resolver_match.url_name
        return super().dispatch(request, *args, **kwargs)

    def has_add_permission(self):
        return self.roles.get(self.url_name) and self.roles[self.url_name] & self.relevant_roles

    def has_change_permission(self, comment: 'CommentEntry'):
        return (
            self.roles.get(self.url_name)
            and self.roles[self.url_name] & self.relevant_roles
            and comment.author == self.request.user.person
        )

    def has_delete_permission(self, comment):
        return self.has_change_permission(comment)

    def get_queryset(self):
        queryset = super().get_queryset()

        tags = self.request.query_params.get('tags', '')

        # Apply the 'contained_by' filter (in addition to the default `contains` filter) to retrieve the comments whose
        # the tags are exactly the same as those requested
        if tags:
            queryset = queryset.filter(tags__contained_by=tags.split(','))

        return queryset
