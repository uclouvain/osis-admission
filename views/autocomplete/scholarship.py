# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db.models import Q
from rules.contrib.views import LoginRequiredMixin

from reference.models.scholarship import Scholarship

__all__ = [
    'ScholarshipAutocomplete',
]


class ScholarshipAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Scholarship.objects.filter(disabled=False)

        scholarship_type = self.forwarded.get('scholarship_type', '')
        if scholarship_type:
            qs = qs.filter(type=scholarship_type)

        if self.q:
            qs = qs.filter(Q(short_name__icontains=self.q) | Q(long_name__icontains=self.q))

        return qs

    def get_results(self, context):
        """Return data for the 'results' key of the response."""
        return [
            {
                'id': str(scholarship.uuid),
                'text': scholarship.long_name or scholarship.short_name,
            }
            for scholarship in context['object_list']
        ]
