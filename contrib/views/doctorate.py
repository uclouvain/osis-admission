# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView, TemplateView

from admission.contrib.models import DoctorateAdmission

__all__ = [
    "DoctorateAdmissionCancelView",
    "DoctorateAdmissionListView",
]


class DoctorateAdmissionCancelView(DeleteView):
    model = DoctorateAdmission
    success_url = reverse_lazy("admission:doctorate-list")
    success_message = _("Doctorate admission was successfully deleted")

    def delete(self, request, *args, **kwargs):
        # SuccessMessageMixin won't work with DeleteView, check next Django version?
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


class DoctorateAdmissionListView(TemplateView):
    template_name = "admission/doctorate/admission_doctorate_list.html"
