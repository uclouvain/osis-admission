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

from django.views.generic import TemplateView
from rules.contrib.views import LoginRequiredMixin

from admission.templatetags.admission import CONTEXT_DOCTORATE, CONTEXT_GENERAL, CONTEXT_CONTINUING
from admission.utils import (
    get_cached_admission_perm_obj,
    get_cached_continuing_education_admission_perm_obj,
    get_cached_general_education_admission_perm_obj,
)
from admission.views.common.mixins import LoadDossierViewMixin
from osis_history.contrib.mixins import HistoryEntryListAPIMixin

from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    "HistoryAPIView",
    "HistoryView",
    "HistoryAllView",
]
__namespace__ = False


class HistoryAPIView(LoginRequiredMixin, APIPermissionRequiredMixin, HistoryEntryListAPIMixin):
    urlpatterns = 'history-api'
    permission_mapping = {
        'GET': 'admission.view_historyentry',
    }

    def get_permission_object(self):
        current_context = self.request.resolver_match.namespaces[1]

        return {
            CONTEXT_DOCTORATE: get_cached_admission_perm_obj,
            CONTEXT_GENERAL: get_cached_general_education_admission_perm_obj,
            CONTEXT_CONTINUING: get_cached_continuing_education_admission_perm_obj,
        }[current_context](self.kwargs['uuid'])


class HistoryView(LoadDossierViewMixin, TemplateView):
    urlpatterns = 'history'
    template_name = 'admission/details/history.html'
    permission_required = 'admission.view_historyentry'
    extra_context = {'tag': 'status-changed'}


class HistoryAllView(LoadDossierViewMixin, TemplateView):
    urlpatterns = 'history-all'
    template_name = 'admission/details/history.html'
    permission_required = 'admission.view_historyentry'
