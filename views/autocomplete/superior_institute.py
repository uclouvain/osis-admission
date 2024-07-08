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
from django.db.models import F

from base.models.entity_version import EntityVersion
from base.models.enums.establishment_type import EstablishmentTypeEnum
from reference.api.views.university import UniversityFilter

__all__ = [
    'SuperiorInstituteAutocomplete',
]


def format_address(street='', street_number='', postal_code='', city='', country=''):
    """Return the concatenation of the specified street, street number, postal code, city and country."""
    address_parts = [
        f'{street} {street_number}',
        f'{postal_code} {city}',
        country,
    ]
    return ', '.join(filter(lambda part: part and len(part) > 1, address_parts))


def format_school_title(school):
    """Return the concatenation of the school name and city."""
    return '{} <span class="school-address">{}</span>'.format(
        school.name,
        format_address(
            street=school.street,
            street_number=school.street_number,
            postal_code=school.zipcode,
            city=school.city,
        ),
    )


class SuperiorInstituteAutocomplete(autocomplete.Select2QuerySetView):
    urlpatterns = 'superior-institute'

    def get_queryset(self):
        queryset = EntityVersion.objects.filter(
            entity__organization__establishment_type__in=[
                EstablishmentTypeEnum.UNIVERSITY.name,
                EstablishmentTypeEnum.NON_UNIVERSITY_HIGHER.name,
            ],
            parent__isnull=True,
        ).annotate(
            organization_id=F('entity__organization_id'),
            organization_uuid=F('entity__organization__uuid'),
            organization_acronym=F('entity__organization__acronym'),
            organization_community=F('entity__organization__community'),
            organization_establishment_type=F('entity__organization__establishment_type'),
            name=F('entity__organization__name'),
            city=F('entityversionaddress__city'),
            street=F('entityversionaddress__street'),
            street_number=F('entityversionaddress__street_number'),
            zipcode=F('entityversionaddress__postal_code'),
        )

        queryset = UniversityFilter.filter_by_active(queryset, None, True)
        queryset = UniversityFilter.search_method(queryset, None, self.q)

        country = self.forwarded.get('country')

        if country:
            queryset = queryset.filter(entityversionaddress__country__iso_code=country)

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
