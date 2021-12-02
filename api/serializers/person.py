# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.db import models
from rest_framework import serializers

from admission.api.serializers.fields import ActionLinksField, ACTION_LINKS
from base.api.serializers.academic_year import RelatedAcademicYearField
from reference.api.serializers.country import RelatedCountryField
from base.models.person import Person

__all__ = [
    "PersonIdentificationSerializer",
]


class PersonIdentificationSerializer(serializers.ModelSerializer):
    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping
    serializer_field_mapping[models.UUIDField] = serializers.CharField

    last_registration_year = RelatedAcademicYearField(required=False)
    birth_country = RelatedCountryField(required=False)
    country_of_citizenship = RelatedCountryField(required=False)

    # links = ActionLinksField(actions={
    # Personal data
    # 'retrieve_proposition_person': ACTION_LINKS['retrieve_proposition_person'],
    # 'update_proposition_person': ACTION_LINKS['update_proposition_person'],
    # 'retrieve_proposition_coordinates': ACTION_LINKS['retrieve_proposition_person'],
    # 'update_proposition_coordinates': ACTION_LINKS['update_proposition_coordinates'],
    # Previous experience
    # 'retrieve_secondary_studies': ACTION_LINKS['retrieve_secondary_studies'],
    # 'update_secondary_studies': ACTION_LINKS['update_secondary_studies'],
    # Doctorate
    # 'retrieve_proposition': ACTION_LINKS['retrieve_proposition'],
    # 'update_proposition': ACTION_LINKS['update_proposition'],
    # })

    class Meta:
        model = Person
        fields = [
            # Signalétique
            'first_name',
            'middle_name',
            'last_name',
            'first_name_in_use',
            'birth_date',
            'birth_year',
            'birth_country',
            'birth_place',
            'country_of_citizenship',
            'language',
            'sex',
            'gender',
            'id_photo',

            # Pièce d'identité
            'id_card',
            'passport',
            'national_number',
            'id_card_number',
            'passport_number',
            'passport_expiration_date',

            # Inscrit ?
            'last_registration_year',
        ]
        extra_kwargs = {
            'birth_year': {'min_value': 1000, 'max_value': 2999}
        }

    def include_extra_kwargs(self, kwargs, extra_kwargs):
        # Make all fields optional
        extra_kwargs['required'] = False
        return super().include_extra_kwargs(kwargs, extra_kwargs)

    def build_standard_field(self, field_name, model_field):
        # Make all fields optional
        model_field.blank = True
        return super().build_standard_field(field_name, model_field)
