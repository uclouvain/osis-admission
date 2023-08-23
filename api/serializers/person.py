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
from django.db import models
from rest_framework import serializers

from base.api.serializers.academic_year import RelatedAcademicYearField
from base.models.person import Person
from reference.api.serializers.country import RelatedCountryField

__all__ = [
    "PersonIdentificationSerializer",
]

from reference.services.belgian_niss_validator import BelgianNISSValidatorService


class PersonIdentificationSerializer(serializers.ModelSerializer):
    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping
    serializer_field_mapping[models.UUIDField] = serializers.CharField

    last_registration_year = RelatedAcademicYearField(required=False)
    birth_country = RelatedCountryField(required=False)
    country_of_citizenship = RelatedCountryField(required=False)

    class Meta:
        model = Person
        fields = [
            # Signalétique
            'first_name',
            'middle_name',
            'last_name',
            'birth_date',
            'birth_year',
            'birth_country',
            'birth_place',
            'country_of_citizenship',
            'language',
            'sex',
            'gender',
            'civil_state',
            'id_photo',
            # Pièce d'identité
            'id_card',
            'passport',
            'national_number',
            'id_card_number',
            'passport_number',
            'id_card_expiry_date',
            'passport_expiry_date',
            # Inscrit ?
            'last_registration_year',
            'last_registration_id',
        ]
        extra_kwargs = {'birth_year': {'min_value': 1900, 'max_value': 2999}}

    def include_extra_kwargs(self, kwargs, extra_kwargs):
        # Make all fields optional
        extra_kwargs['required'] = False
        return super().include_extra_kwargs(kwargs, extra_kwargs)

    def build_standard_field(self, field_name, model_field):
        # Make all fields optional
        model_field.blank = True
        return super().build_standard_field(field_name, model_field)

    def validate(self, data):
        if data.get('national_number'):
            BelgianNISSValidatorService(
                data['national_number'],
                data['gender'],
                data['birth_date'],
                data['birth_year'],
            ).validate()
        return data
