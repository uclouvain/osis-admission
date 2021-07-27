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
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView

from admission.contrib.filters import DoctorateAdmissionFilter
from admission.contrib.forms import DoctorateAdmissionCreateOrUpdateForm
from admission.contrib.models import DoctorateAdmission
from admission.contrib.serializers import DoctorateAdmissionReadSerializer
from base.utils.search import SearchMixin


class DoctorateAdmissionCreateView(
    SuccessMessageMixin,
    CreateView,
):
    model = DoctorateAdmission
    template_name = "admission/doctorate/admission_doctorate_create.html"
    form_class = DoctorateAdmissionCreateOrUpdateForm
    success_message = _("Record successfully saved")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user
        if user.is_authenticated and hasattr(user, "person"):
            # Add user.person to the form kwargs and do the logic in the form
            kwargs.update({"author": user.person})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse("admissions:doctorate-list")
        return context


class DoctorateAdmissionDeleteView(DeleteView):
    model = DoctorateAdmission
    success_url = reverse_lazy("admissions:doctorate-list")
    success_message = _("Doctorate admission was successfully deleted")

    def delete(self, request, *args, **kwargs):
        # SuccessMessageMixin won't work with DeleteView, check next Django version?
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


class DoctorateAdmissionDetailView(DetailView):
    model = DoctorateAdmission
    template_name = "admission/doctorate/admission_doctorate_detail.html"


class DoctorateAdmissionListView(SearchMixin, FilterView):
    model = DoctorateAdmission
    template_name = "admission/doctorate/admission_doctorate_list.html"
    context_object_name = "doctorates"
    filterset_class = DoctorateAdmissionFilter
    serializer_class = DoctorateAdmissionReadSerializer

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context["paginator"].count == 0 and self.request.GET:
            messages.add_message(self.request, messages.WARNING, _("No result!"))
            # FIXME When getting no results, the warning message above is well displayed
            # But doing a research that is returning results just after still shows the message
        context.update({
            "items_per_page": context["paginator"].per_page,
        })
        return context


class DoctorateAdmissionUpdateView(SuccessMessageMixin, UpdateView):
    model = DoctorateAdmission
    template_name = "admission/doctorate/admission_doctorate_update.html"
    form_class = DoctorateAdmissionCreateOrUpdateForm
    success_message = _("Doctorate admission was successfully updated")
