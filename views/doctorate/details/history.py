# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.views.generic import TemplateView
from rules.contrib.views import LoginRequiredMixin

from admission.utils import get_cached_admission_perm_obj
from admission.views.doctorate.mixins import LoadDossierViewMixin
from osis_history.contrib.mixins import HistoryEntryListAPIMixin

from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    "DoctorateHistoryAPIView",
    "DoctorateHistoryView",
    "DoctorateHistoryAllView",
]
__namespace__ = False


class DoctorateHistoryAPIView(LoginRequiredMixin, APIPermissionRequiredMixin, HistoryEntryListAPIMixin):
    urlpatterns = 'history-api'
    permission_mapping = {
        'GET': 'osis_history.view_historyentry',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])


class DoctorateHistoryView(LoadDossierViewMixin, TemplateView):
    urlpatterns = 'history'
    template_name = 'admission/doctorate/details/history.html'
    permission_required = 'osis_history.view_historyentry'
    extra_context = {'tag': 'status-changed'}


class DoctorateHistoryAllView(LoadDossierViewMixin, TemplateView):
    urlpatterns = 'history-all'
    template_name = 'admission/doctorate/details/history.html'
    permission_required = 'osis_history.view_historyentry'
