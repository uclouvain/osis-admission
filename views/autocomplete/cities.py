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
from rules.contrib.views import LoginRequiredMixin

__all__ = [
    'CitiesAutocomplete',
]

from reference.models.zipcode import ZipCode


class CitiesAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = ZipCode.objects.all()

        postal_code = self.forwarded.get('postal_code', '')
        if postal_code:
            qs = qs.filter(zip_code=postal_code)

        if self.q:
            qs = qs.filter(municipality__icontains=self.q)

        return qs.values('municipality', 'zip_code').order_by(
            'municipality',
            'zip_code',
        )

    def get_results(self, context):
        """Return data for the 'results' key of the response."""
        return [
            {
                'id': city.get('zip_code'),
                'text': f"{city.get('municipality')} - {city.get('zip_code')}",
            }
            for city in context['object_list']
        ]
