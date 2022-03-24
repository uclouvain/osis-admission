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
from dal import autocomplete
from django.conf import settings
from django.utils.translation import get_language
from rules.contrib.views import LoginRequiredMixin

from osis_role.contrib.views import PermissionRequiredMixin
from reference.models.country import Country


class CountriesAutocomplete(LoginRequiredMixin, PermissionRequiredMixin, autocomplete.Select2QuerySetView):

    permission_required = 'admission.can_access_doctorateadmission'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name_field = 'name' if get_language() == settings.LANGUAGE_CODE else 'name_en'

    def get_queryset(self):
        search_term = self.request.GET.get('q', '')
        return Country.objects.filter(
            **{'{}__icontains'.format(self.name_field): search_term}
        ).values(self.name_field, 'iso_code').order_by(self.name_field)

    def get_results(self, context):
        """Return data for the 'results' key of the response."""
        return [
            {
                'id': country.get('iso_code'),
                'text': country.get(self.name_field),
            } for country in context['object_list']
        ]
