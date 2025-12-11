# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from admission.ddd.admission.shared_kernel.domain.service.i_calendrier_inscription import (
    ICalendrierInscription,
)
from admission.models import GeneralEducationAdmission


class PoolQuestionsSerializer(serializers.ModelSerializer):
    reorientation_pool_end_date = serializers.DateTimeField(read_only=True, allow_null=True)
    reorientation_pool_academic_year = serializers.IntegerField(read_only=True, allow_null=True)
    modification_pool_end_date = serializers.DateTimeField(read_only=True, allow_null=True)
    modification_pool_academic_year = serializers.IntegerField(read_only=True, allow_null=True)
    non_resident_quota_pool_start_date = serializers.DateField(read_only=True, allow_null=True)
    non_resident_quota_pool_start_time = serializers.TimeField(read_only=True, allow_null=True)
    non_resident_quota_pool_end_date = serializers.DateField(read_only=True, allow_null=True)
    non_resident_quota_pool_end_time = serializers.TimeField(read_only=True, allow_null=True)

    class Meta:
        model = GeneralEducationAdmission
        fields = [
            'is_belgian_bachelor',
            'is_external_reorientation',
            'regular_registration_proof',
            'reorientation_form',
            'is_external_modification',
            'registration_change_form',
            'regular_registration_proof_for_registration_change',
            'is_non_resident',
            'residence_certificate',
            'residence_student_form',
            'non_resident_file',
            'non_resident_with_second_year_enrolment',
            'non_resident_with_second_year_enrolment_form',
            'reorientation_pool_end_date',
            'reorientation_pool_academic_year',
            'modification_pool_end_date',
            'modification_pool_academic_year',
            'non_resident_quota_pool_start_date',
            'non_resident_quota_pool_start_time',
            'non_resident_quota_pool_end_date',
            'non_resident_quota_pool_end_time',
        ]
