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

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from admission.contrib.models import DoctorateAdmission, AdmissionType
from base.models.person import Person


class DoctorateAdmissionReadSerializer(serializers.ModelSerializer):
    url = serializers.ReadOnlyField(source="get_absolute_url")
    type = serializers.ReadOnlyField(source="get_type_display")
    candidate = serializers.StringRelatedField()
    author = serializers.StringRelatedField()

    class Meta:
        model = DoctorateAdmission
        fields = [
            "uuid",
            "url",
            "type",
            "candidate",
            "comment",
            "author",
            "created",
            "modified",
        ]


class DoctorateAdmissionWriteSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=AdmissionType.choices())
    candidate = serializers.PrimaryKeyRelatedField(
        label=_("Candidate"), queryset=Person.objects.all()
    )

    def create(self, validated_data):
        validated_data['author'] = self.context["request"].user.person
        return super().create(validated_data)

    class Meta:
        model = DoctorateAdmission
        fields = [
            "type",
            "candidate",
            "comment",
        ]
