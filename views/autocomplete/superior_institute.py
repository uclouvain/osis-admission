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

from dal import autocomplete

from admission.utils import get_superior_institute_queryset, format_school_title
from base.utils.eval import eval_bool
from osis_profile import BE_ISO_CODE
from reference.api.views.university import UniversityFilter

__namespace__ = False

__all__ = [
    'SuperiorInstituteAutocomplete',
    'SuperiorInstituteUuidAutocomplete',
]


class SuperiorInstituteAutocomplete(autocomplete.Select2QuerySetView):
    urlpatterns = 'superior-institute'

    def get_queryset(self):
        queryset = get_superior_institute_queryset()

        queryset = UniversityFilter.filter_by_active(queryset, None, True)
        queryset = UniversityFilter.search_method(queryset, None, self.q)

        country = self.forwarded.get('country')
        is_belgian = eval_bool(self.forwarded.get('is_belgian'))
        if country:
            queryset = queryset.filter(entityversionaddress__country__iso_code=country)
        elif is_belgian:
            queryset = queryset.filter(entityversionaddress__country__iso_code=BE_ISO_CODE)

        queryset = queryset.order_by('name', 'organization_uuid', '-start_date',).distinct(
            'name',
            'organization_uuid',
        )

        return queryset

    def get_results(self, context):
        return [
            {
                'id': self.get_result_value(result),
                'text': self.get_result_label(result),
                'community': result.organization_community,
                'establishment_type': result.organization_establishment_type,
            }
            for result in context['object_list']
        ]

    def get_result_label(self, result):
        return format_school_title(result)

    def get_result_value(self, result):
        return result.organization_id


class SuperiorInstituteUuidAutocomplete(SuperiorInstituteAutocomplete):
    urlpatterns = 'superior-institute-uuid'

    def get_result_value(self, result):
        return result.organization_uuid
