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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import NON_FIELD_ERRORS
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.generic import ListView

from admission.ddd.projet_doctoral.validation.commands import FiltrerDemandesQuery
from admission.forms.doctorate.cdd.filter import FilterForm
from admission.auth.mixins import CddRequiredMixin
from base.utils.htmx import HtmxMixin
from infrastructure.messages_bus import message_bus_instance

# Enums that are used in the template
from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixStatutProposition
from admission.ddd.projet_doctoral.preparation.domain.model._financement import ChoixTypeFinancement
from admission.ddd.projet_doctoral.validation.domain.model._enums import ChoixStatutCDD, ChoixStatutSIC


class CddDoctorateAdmissionList(LoginRequiredMixin, CddRequiredMixin, HtmxMixin, ListView):
    raise_exception = True

    template_name = 'admission/doctorate/cdd/list.html'
    htmx_template_name = 'admission/doctorate/cdd/list_block.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form = None

    @staticmethod
    def htmx_render_form_errors(request, form):
        """Returns an HttpResponse containing the errors of the form grouped by field."""
        formatted_errors = [
            (form.fields.get(field_name).label if field_name != NON_FIELD_ERRORS else _('General'), errors)
            for field_name, errors in form.errors.items()
        ]

        return render(
            status=400,
            request=request,
            template_name='admission/includes/form_errors.html',
            context={
                'errors': formatted_errors,
            },
        )

    def get(self, request, *args, **kwargs):
        self.form = FilterForm(user=self.request.user, data=self.request.GET or None)

        if not self.form.is_valid() and self.request.htmx:
            return self.htmx_render_form_errors(request, self.form)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.form
        return context

    def get_paginate_by(self, queryset):
        return self.request.GET.get('page_size')

    def get_queryset(self):
        if not self.form.is_bound or not self.form.is_valid():
            return []

        filters = self.form.cleaned_data

        filters.pop('page_size', None)

        # Order the queryset
        ordering_field = self.request.GET.get('o')
        if ordering_field:
            filters['tri_inverse'] = ordering_field[0] == '-'
            filters['champ_tri'] = ordering_field.lstrip('-')

        return message_bus_instance.invoke(
            FiltrerDemandesQuery(
                **filters,
            )
        )
