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

from admission.ddd.admission.domain.service.i_calendrier_inscription import (
    ICalendrierInscription,
)
from admission.ddd.admission.domain.validator.exceptions import (
    ResidenceAuSensDuDecretNonDisponiblePourInscriptionException,
)
from admission.models import GeneralEducationAdmission


class PoolQuestionsSerializer(serializers.ModelSerializer):
    reorientation_pool_end_date = serializers.DateTimeField(read_only=True, allow_null=True)
    reorientation_pool_academic_year = serializers.IntegerField(read_only=True, allow_null=True)
    modification_pool_end_date = serializers.DateTimeField(read_only=True, allow_null=True)
    modification_pool_academic_year = serializers.IntegerField(read_only=True, allow_null=True)
    forbid_enrolment_limited_course_for_non_resident = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.STR)
    def get_forbid_enrolment_limited_course_for_non_resident(self, obj):
        return ResidenceAuSensDuDecretNonDisponiblePourInscriptionException.get_message(
            nom_formation_fr=obj.training.title,
            nom_formation_en=obj.training.title_english,
        )

    def get_field_names(self, *args, **kwargs):
        field_names = super().get_field_names(*args, **kwargs)

        # Add or remove the forbid enrolment limited course for non resident message depending of what is desired
        if 'forbid_enrolment_limited_course_for_non_resident' in field_names:
            if not ICalendrierInscription.INTERDIRE_INSCRIPTION_ETUDES_CONTINGENTES_POUR_NON_RESIDENT:
                field_names.remove('forbid_enrolment_limited_course_for_non_resident')
        elif ICalendrierInscription.INTERDIRE_INSCRIPTION_ETUDES_CONTINGENTES_POUR_NON_RESIDENT:
            field_names.append('forbid_enrolment_limited_course_for_non_resident')

        return field_names

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
            'reorientation_pool_end_date',
            'reorientation_pool_academic_year',
            'modification_pool_end_date',
            'modification_pool_academic_year',
            'forbid_enrolment_limited_course_for_non_resident',
        ]
