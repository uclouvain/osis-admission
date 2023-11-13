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
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from osis_comment.contrib.mixins import CommentEntryAPIMixin
from osis_comment.models import CommentEntry

from admission.auth.roles.central_manager import CentralManager
from admission.auth.roles.program_manager import ProgramManager
from admission.auth.roles.sic_management import SicManagement
from admission.views.doctorate.mixins import LoadDossierViewMixin
from backoffice.settings.base import CKEDITOR_CONFIGS
from base.models.utils.utils import ChoiceEnum
from osis_role.contrib.permissions import _get_roles_assigned_to_user

__all__ = [
    "AdmissionCommentsView",
    "AdmissionCommentApiView",
    "COMMENT_TAG_SIC",
    "COMMENT_TAG_FAC",
    "COMMENT_TAG_GLOBAL",
    "CheckListTagsEnum",
]
__namespace__ = False

COMMENT_TAG_SIC = 'SIC'
COMMENT_TAG_FAC = 'FAC'
COMMENT_TAG_GLOBAL = 'GLOBAL'
CHECKLIST_TABS_WITH_SIC_AND_FAC_COMMENTS = {
    'decision_facultaire',
}


class CheckListTagsEnum(ChoiceEnum):
    assimilation = _('Belgian student status')
    financabilite = _('Financeability')
    frais_dossier = _('Application fee')
    choix_formation = _('Course choice')
    parcours_anterieur = _('Previous experience')
    donnees_personnelles = _('Personal data')
    specificites_formation = _('Training specificities')
    decision_facultaire = _('Decision of the faculty')
    decision_sic = _('Decision of SIC')


class AdmissionCommentsView(LoadDossierViewMixin, TemplateView):
    urlpatterns = 'comments'
    permission_required = 'admission.view_enrolment_application'
    template_name = "admission/details/comments.html"
    extra_context = {
        'COMMENT_TAG_FAC': f'{COMMENT_TAG_FAC},{COMMENT_TAG_GLOBAL}',
        'COMMENT_TAG_SIC': f'{COMMENT_TAG_SIC},{COMMENT_TAG_GLOBAL}',
        'checklist_tags': CheckListTagsEnum.choices(),
        'ckeditor_config': CKEDITOR_CONFIGS['minimal'],
        'CHECKLIST_TABS_WITH_SIC_AND_FAC_COMMENTS': CHECKLIST_TABS_WITH_SIC_AND_FAC_COMMENTS,
    }


class AdmissionCommentApiView(CommentEntryAPIMixin):
    urlpatterns = {
        'sic-comments': [f"sic-comments", f"sic-comments/<uuid:comment_uuid>"],
        'fac-comments': [f"fac-comments", f"fac-comments/<uuid:comment_uuid>"],
        'other-comments': [f"other-comments", f"other-comments/<uuid:comment_uuid>"],
    }
    roles = {
        'sic-comments': {SicManagement, CentralManager},
        'fac-comments': {ProgramManager},
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
