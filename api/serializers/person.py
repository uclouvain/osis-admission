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

# ##############################################################################
#
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

from base.models.person import Person
from reference.models.country import Country

__all__ = [
    "PersonIdentificationSerializer",
    "CountrySerializer",
]


class PersonIdentificationSerializer(serializers.ModelSerializer):
    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping
    serializer_field_mapping[models.UUIDField] = serializers.CharField

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

    def include_extra_kwargs(self, kwargs, extra_kwargs):
        # Make all fields optional
        extra_kwargs['required'] = False
        return super().include_extra_kwargs(kwargs, extra_kwargs)

    def build_standard_field(self, field_name, model_field):
        # Make all fields optional
        model_field.blank = True
        return super().build_standard_field(field_name, model_field)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            'pk',
            'iso_code',
            'name',
            'name_en',
        ]
