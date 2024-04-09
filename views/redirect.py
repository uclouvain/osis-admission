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
from django.utils.functional import cached_property
from django.views.generic import RedirectView

from admission.ddd.admission.formation_generale.domain.model.enums import STATUTS_PROPOSITION_GENERALE_SOUMISE
from admission.views.common.detail_tabs.documents import DocumentView
from admission.views.common.detail_tabs.person import AdmissionPersonDetailView
from admission.views.common.mixins import AdmissionViewMixin
from admission.views.general_education.details.checklist import ChecklistView

__all__ = ['AdmissionRedirectView']
__namespace__ = False


class AdmissionRedirectView(AdmissionViewMixin, RedirectView):
    urlpatterns = {
        'doctorate': 'doctorate/<uuid:uuid>/',
        'general-education': 'general-education/<uuid:uuid>/',
        'continuing-education': 'continuing-education/<uuid:uuid>/',
    }

    # To change after the implementation of the tabs for the specified context
    available_checklist_by_context = {
        'doctorate': False,
        'general-education': True,
        'continuing-education': True,
    }
    available_documents_by_context = {
        'doctorate': False,
        'general-education': True,
        'continuing-education': False,
    }

    @cached_property
    def can_access_checklist(self):
        self.permission_required = ChecklistView.permission_required
        return (
            self.available_checklist_by_context[self.current_context]
            and self.admission.status in STATUTS_PROPOSITION_GENERALE_SOUMISE
            and super().has_permission()
        )

    @cached_property
    def can_access_documents_management(self):
        self.permission_required = DocumentView.permission_required
        return self.available_documents_by_context[self.current_context] and super().has_permission()

    @cached_property
    def can_access_person_tab(self):
        self.permission_required = AdmissionPersonDetailView.permission_required
        return super().has_permission()

    def has_permission(self):
        return self.can_access_checklist or self.can_access_documents_management or self.can_access_person_tab

    @property
    def current_context(self):
        return self.request.resolver_match.url_name

    @property
    def pattern_name(self):
        if self.can_access_checklist:
            tab_name = 'checklist'
        elif self.can_access_documents_management:
            tab_name = 'documents'
        else:
            tab_name = 'person'
        return f"admission:{self.current_context}:{tab_name}"
