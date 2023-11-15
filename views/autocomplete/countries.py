# ##############################################################################
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
# ##############################################################################
from dal import autocomplete
from django.conf import settings
from django.utils.functional import cached_property
from django.utils.translation import get_language
from rules.contrib.views import LoginRequiredMixin

from reference.models.country import Country

__all__ = [
    'CountriesAutocomplete',
]


class CountriesAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """
    Return a list of countries based on the search term and the active flag. The returned ids are the model pks.
    """

    @cached_property
    def id_field(self):
        return self.forwarded.get('id_field', 'pk')

    @cached_property
    def name_field(self):
        return 'name' if get_language() == settings.LANGUAGE_CODE_FR else 'name_en'

    def get_queryset(self):
        search_term = self.request.GET.get('q', '')

        qs = Country.objects.filter(**{'{}__icontains'.format(self.name_field): search_term})

        active = self.forwarded.get('active', None)
        if active is not None:
            qs = qs.filter(active=active)

        return qs.order_by(self.name_field)

    def get_result_label(self, result):
        return getattr(result, self.name_field)

    def get_result_value(self, result):
        return getattr(result, self.id_field)

    def get_results(self, context):
        return [
            {
                'id': getattr(result, self.id_field),
                'text': getattr(result, self.name_field),
                'selected_text': getattr(result, self.name_field),
                'european_union': result.european_union,
            }
            for result in context['object_list']
        ]
