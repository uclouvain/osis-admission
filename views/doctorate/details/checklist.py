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
from django.shortcuts import resolve_url
from django.views.generic import TemplateView

from admission.forms.doctorate.cdd.send_mail import CddDoctorateSendMailForm
from admission.views.common.mixins import LoadDossierViewMixin

__namespace__ = False

__all__ = [
    'ChecklistView',
]


class CheckListDefaultContextMixin(LoadDossierViewMixin):
    pass


class ChecklistView(
    CheckListDefaultContextMixin,
    TemplateView,
):
    urlpatterns = 'checklist'
    template_name = "admission/doctorate/details/checklist.html"
    permission_required = 'admission.view_checklist'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add forms
        context['send_email_form'] = CddDoctorateSendMailForm(
            admission=self.admission,
            view_url=resolve_url('admission:doctorate:send-mail', self.admission_uuid),
        )

        return context
