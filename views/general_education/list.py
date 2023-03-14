##############################################################################
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
##############################################################################
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.functional import cached_property
from django.views.generic import ListView

from admission.contrib.models import GeneralEducationAdmissionProxy
from admission.forms.doctorate.cdd.filter import BaseFilterForm
from base.utils.htmx import HtmxMixin

__all__ = [
    "GeneralAdmissionList",
]


class GeneralAdmissionList(LoginRequiredMixin, PermissionRequiredMixin, HtmxMixin, ListView):
    raise_exception = True
    template_name = 'admission/general/list.html'
    htmx_template_name = 'admission/general/list_block.html'
    permission_required = 'admission.view_general_dossiers'

    @cached_property
    def form(self):
        return BaseFilterForm(self.request.user, data=self.request.GET or None)

    def get_paginate_by(self, queryset):
        return self.form.data.get('taille_page', 10)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.form
        return context

    def get_queryset(self):
        # TODO Wait for GetAdmissionsQuery
        return GeneralEducationAdmissionProxy.objects.for_dto().all()
