# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from dal import autocomplete
from django.db.models import Q

from admission.views.autocomplete.superior_institute import format_school_title
from reference.api.views.high_school import HighSchoolList

__all__ = [
    'HighSchoolInstituteAutocomplete',
]


class HighSchoolInstituteAutocomplete(autocomplete.Select2QuerySetView):
    urlpatterns = 'high-school-institute'

    def get_queryset(self):
        queryset = HighSchoolList.queryset.filter(is_active=True)

        if self.q:
            queryset = queryset.filter(
                Q(name__unaccent__icontains=self.q)
                | Q(entity__entityversion__entityversionaddress__postal_code__icontains=self.q)
                | Q(entity__entityversion__entityversionaddress__city__unaccent__icontains=self.q)
            )

        community = self.forwarded.get('community')

        if community:
            queryset = queryset.filter(community=community)

        return queryset.order_by('name')

    def get_result_label(self, result):
        return format_school_title(school=result)
