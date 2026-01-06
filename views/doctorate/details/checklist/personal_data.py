# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.forms.forms import Form
from django.views.generic import FormView

from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    OngletsChecklist,
)
from admission.views.common.detail_tabs.checklist import change_admission_status
from admission.views.common.mixins import AdmissionFormMixin, LoadDossierViewMixin
from base.utils.htmx import HtmxPermissionRequiredMixin

__all__ = [
    'PersonalDataChangeStatusView',
]

__namespace__ = None


class PersonalDataChangeStatusView(
    AdmissionFormMixin,
    LoadDossierViewMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    urlpatterns = {'personal-data-change-status': 'personal-data-change-status/<str:status>'}
    template_name = 'admission/general_education/includes/checklist/personal_data.html'
    form_class = Form

    def get_permission_required(self):
        return (
            {
                'INITIAL_CANDIDAT': 'admission.change_personal_data_checklist_status_to_be_processed',
                'GEST_EN_COURS': 'admission.change_personal_data_checklist_status_cleaned',
            }.get(self.kwargs.get('status'), 'admission.change_checklist'),
        )

    def form_valid(self, form):
        admission = self.get_permission_object()

        extra = {}
        if 'fraud' in self.request.POST:
            extra['fraud'] = self.request.POST['fraud']

        change_admission_status(
            tab=OngletsChecklist.donnees_personnelles.name,
            admission_status=self.kwargs['status'],
            extra=extra,
            admission=admission,
            author=self.request.user.person,
            replace_extra=True,
        )

        return super().form_valid(form)
