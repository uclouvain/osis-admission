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
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import ListView
from django.views.generic.edit import FormMixin

from admission.constants import DEFAULT_PAGINATOR_SIZE
from admission.ddd.admission.shared_kernel.commands import ListerToutesDemandesQuery
from admission.forms.admission.filter import AllAdmissionsFilterForm
from admission.models.working_list import UNCHANGED_KEY
from admission.utils import add_messages_into_htmx_response
from admission.views import ListPaginator
from base.views.common import display_error_messages
from infrastructure.messages_bus import message_bus_instance
from osis_common.utils.htmx import HtmxMixin

__all__ = [
    "AdmissionList",
]


class BaseAdmissionList(LoginRequiredMixin, PermissionRequiredMixin, HtmxMixin, FormMixin, ListView):
    raise_exception = True
    filtering_query_class = None
    htmx_template_name = None
    parameters_cache_timeout = None
    result_cache_timeout = 60 * 60 * 24  # 1 day

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form = None
        self.filters = {}

    @property
    def cache_key(self):
        return f"cache_filter_{self.request.user.id}_{self.request.path}"

    @classmethod
    def cache_key_for_result(cls, user_id):
        return f"cache_filter_result_{user_id}"

    @staticmethod
    def htmx_render_form_errors(request, form):
        """Display the form errors through the django messages."""
        display_error_messages(
            request=request,
            messages_to_display=[
                '{} - {}'.format(
                    form.fields.get(field_name).label if field_name != NON_FIELD_ERRORS else _('General'),
                    ' '.join(errors),
                )
                for field_name, errors in form.errors.items()
            ],
        )

    def get_context_data(self, **kwargs):
        kwargs['form'] = self.form
        kwargs['filter_form'] = self.form
        kwargs['htmx_template_name'] = self.htmx_template_name
        kwargs['default_form_values'] = {field.name: field.initial for field in self.form if field.initial}
        kwargs['now'] = datetime.datetime.now()
        kwargs['UNCHANGED_KEY'] = UNCHANGED_KEY
        return super().get_context_data(**kwargs)

    def get_paginate_by(self, queryset):
        if self.form.is_valid() and self.form.cleaned_data.get('taille_page'):
            return self.form.cleaned_data.get('taille_page')
        return DEFAULT_PAGINATOR_SIZE

    def additional_command_kwargs(self):
        return {}

    @cached_property
    def query_params(self):
        return self.request.GET or cache.get(self.cache_key)

    def get_form_kwargs(self):
        return {
            'user': self.request.user,
            'data': self.query_params,
            'load_labels': not self.request.htmx,
        }

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()

        if not self.form.is_valid():
            self.object_list = []
            response = self.form_invalid(form=self.form)
            if self.request.htmx:
                self.htmx_render_form_errors(self.request, self.form)
                add_messages_into_htmx_response(request=self.request, response=response)
            return response

        if self.request.GET:
            cache.set(self.cache_key, self.request.GET, timeout=self.parameters_cache_timeout)

        self.filters = self.form.cleaned_data

        self.filters.pop('liste_travail', None)

        if self.query_params:
            # Add page number to kwargs to pass it to the paginator
            self.kwargs['page'] = self.query_params.get('page')

            # Order the queryset if specified
            ordering_field = self.query_params.get('o')

            if ordering_field:
                self.filters['tri_inverse'] = ordering_field[0] == '-'
                self.filters['champ_tri'] = ordering_field.lstrip('-')

        response = super().get(request, *args, **kwargs)

        if self.request.GET:
            cache.set(
                self.cache_key_for_result(user_id=self.request.user.id),
                self.object_list.sorted_elements,
                timeout=self.result_cache_timeout,
            )

        return response

    def get_queryset(self):
        return message_bus_instance.invoke(
            self.filtering_query_class(
                **self.filters,
                **self.additional_command_kwargs(),
            )
        )


class AdmissionList(BaseAdmissionList):
    template_name = 'admission/list/list_all.html'
    htmx_template_name = 'admission/list/list_all_block.html'
    permission_required = 'admission.view_enrolment_applications'
    filtering_query_class = ListerToutesDemandesQuery
    form_class = AllAdmissionsFilterForm
    urlpatterns = 'all-list'
    paginator_class = ListPaginator

    def additional_command_kwargs(self):
        return {
            'demandeur': self.request.user.person.uuid,
        }
