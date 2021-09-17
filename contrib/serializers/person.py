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

from rest_framework import serializers

from base.models.person import Person
from osis_profile.models import Profile

__all__ = [
    "DoctorateAdmissionProfileSerializer",
    "DoctorateAdmissionPersonalInfoSerializer",
    "DoctorateAdmissionPersonTabSerializer",
]


class LaxSerializerMixin:
    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping

    # serializer_field_mapping[FileField] = DocumentField

    def __init__(self, all_fields_optional=True, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.all_fields_optional = all_fields_optional

    def include_extra_kwargs(self, kwargs, extra_kwargs):
        if self.all_fields_optional:
            extra_kwargs['required'] = False
        return super().include_extra_kwargs(kwargs, extra_kwargs)

    def build_standard_field(self, field_name, model_field):
        if self.all_fields_optional:
            model_field.blank = True
        return super().build_standard_field(field_name, model_field)


class DoctorateAdmissionPersonalInfoSerializer(LaxSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = [
            'first_name',
            'last_name',
            'language',
            'birth_date',
        ]


class DoctorateAdmissionProfileSerializer(LaxSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'id_photo',
            'birth_year',
            'birth_place',
            'national_number',
            'id_card_number',
            'passport_number',
            'passport_expiration_date',
            'id_card',
            'passport',
            'iban',
            'bic_swift',
            'bank_holder_name',
            'last_registration_year',
        ]


class DoctorateAdmissionPersonTabSerializer(serializers.Serializer):
    person = DoctorateAdmissionPersonalInfoSerializer(all_fields_optional=False)
    profile = DoctorateAdmissionProfileSerializer(all_fields_optional=False)
