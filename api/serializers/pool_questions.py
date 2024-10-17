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
from rest_framework import serializers

from admission.models import GeneralEducationAdmission
from admission.ddd.admission.domain.service.i_calendrier_inscription import ICalendrierInscription
from admission.ddd.admission.domain.validator.exceptions import (
    ResidenceAuSensDuDecretNonDisponiblePourInscriptionException,
)


class PoolQuestionsSerializer(serializers.ModelSerializer):
    reorientation_pool_end_date = serializers.DateTimeField(read_only=True, allow_null=True)
    modification_pool_end_date = serializers.DateTimeField(read_only=True, allow_null=True)
    forbid_enrolment_limited_course_for_non_resident = serializers.SerializerMethodField()

    def get_forbid_enrolment_limited_course_for_non_resident(self, _):
        return ResidenceAuSensDuDecretNonDisponiblePourInscriptionException.message

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
            'is_external_modification',
            'registration_change_form',
            'is_non_resident',
            'reorientation_pool_end_date',
            'modification_pool_end_date',
            'forbid_enrolment_limited_course_for_non_resident',
        ]
