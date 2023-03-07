##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.messages import error
from django.core.cache import cache
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils.translation import gettext as _
from django.views.generic import ListView

from admission.ddd.admission.commands import ListerToutesDemandesQuery
from admission.forms.admission.filter import AllAdmissionsFilterForm
from base.utils.htmx import HtmxMixin
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    "AdmissionList",
]


class BaseAdmissionList(LoginRequiredMixin, PermissionRequiredMixin, HtmxMixin, ListView):
    raise_exception = True
    DEFAULT_PAGINATOR_SIZE = '10'
    filtering_query_class = None
    form_class = None
    htmx_template_name = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form = None

    @property
    def cache_key(self):
        return "_".join(['cache_filter', str(self.request.user.id), self.request.path])

    @staticmethod
    def htmx_render_form_errors(request, form):
        """Display the form errors through the django messages."""
        for field_name, errors in form.errors.items():
            error(
                request=request,
                message='{} - {}'.format(
                    form.fields.get(field_name).label if field_name != NON_FIELD_ERRORS else _('General'),
                    ' '.join(errors),
                ),
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.form
        context['htmx_template_name'] = self.htmx_template_name
        return context

    def get_paginate_by(self, queryset):
        return self.form.data.get('page_size', self.DEFAULT_PAGINATOR_SIZE)

    def get_form(self):
        if self.form_class:
            return self.form_class
        raise NotImplemented  # pragma: no cover

    def get_queryset(self):
        query_params = self.request.GET.copy()

        ordering_field = query_params.pop('o', None)
        query_params.pop('page', None)

        self.form = self.get_form()(
            user=self.request.user,
            data=query_params or cache.get(self.cache_key) or None,
            load_labels=not self.request.htmx,
        )

        if not self.form.is_valid():
            if self.request.htmx:
                self.htmx_render_form_errors(self.request, self.form)
            return []

        if query_params:
            cache.set(self.cache_key, query_params)

        filters = self.form.cleaned_data

        filters.pop('page_size', None)

        # Order the queryset
        if ordering_field:
            filters['tri_inverse'] = ordering_field[0][0] == '-'
            filters['champ_tri'] = ordering_field[0].lstrip('-')

        return message_bus_instance.invoke(self.filtering_query_class(**filters))


class AdmissionList(BaseAdmissionList):
    template_name = 'admission/list/list_all.html'
    htmx_template_name = 'admission/list/list_all_block.html'
    permission_required = 'admission.view_dossiers'
    filtering_query_class = ListerToutesDemandesQuery
    form_class = AllAdmissionsFilterForm
    urlpatterns = 'all-list'
