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
import datetime

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.settings import api_settings

from admission.api.serializers.pool_questions import PoolQuestionsSerializer
from admission.calendar.admission_calendar import SIGLES_WITH_QUOTA
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import (
    ModificationInscriptionExterneNonConfirmeeException,
    ReorientationInscriptionExterneNonConfirmeeException,
    ResidenceAuSensDuDecretNonRenseigneeException,
)
from admission.ddd.admission.formation_generale.commands import VerifierPropositionQuery
from admission.models import GeneralEducationAdmission
from admission.utils import (
    gather_business_exceptions,
    get_cached_general_education_admission_perm_obj,
)
from base.models.academic_calendar import AcademicCalendar
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from osis_role.contrib.views import APIPermissionRequiredMixin


class PoolQuestionsView(APIPermissionRequiredMixin, RetrieveAPIView):
    name = "pool-questions"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission_specific_question',
        'PUT': 'admission.change_generaleducationadmission_specific_question',
    }
    serializer_class = PoolQuestionsSerializer

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])

    @extend_schema(operation_id='retrieve_pool_questions')
    def get(self, request, *args, **kwargs):
        """Get relevant pool questions"""
        admission = self.get_permission_object()

        # Questions are only for bachelor
        if admission.training.education_group_type.name != TrainingType.BACHELOR.name:
            return Response({})

        # Trigger verification to get exceptions related to pool questions
        error_key = api_settings.NON_FIELD_ERRORS_KEY
        exception_to_check = [
            ResidenceAuSensDuDecretNonRenseigneeException.status_code,
            ReorientationInscriptionExterneNonConfirmeeException.status_code,
            ModificationInscriptionExterneNonConfirmeeException.status_code,
        ]
        current_error_statuses = [
            e['status_code']
            for e in gather_business_exceptions(VerifierPropositionQuery(self.kwargs['uuid'])).get(error_key, [])
        ]
        if (
            # Display nothing if no related exceptions was raised
            not any(status_code in current_error_statuses for status_code in exception_to_check)
            # And nothing was specified before
            and admission.is_non_resident is None
            and admission.is_belgian_bachelor is None
        ):
            return Response({})

        # Load current reorientation and modification calendar for their finishing dates
        pools = {
            "modification_pool": AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_ENROLLMENT_CHANGE.name,
            "reorientation_pool": AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_REORIENTATION.name,
        }
        calendars = {
            calendar['reference']: {
                'end_date': calendar.get('end_date'),
                'academic_year': calendar.get('data_year__year'),
            }
            for calendar in (
                AcademicCalendar.objects.filter(
                    start_date__lte=datetime.date.today(),
                    end_date__gte=datetime.date.today(),
                    reference__in=pools.values(),
                ).values('reference', 'end_date', 'data_year__year')
            )
        }

        field_questions_to_display = []

        for base_field_name, calendar_name in pools.items():
            current_calendar = calendars.get(calendar_name, {})

            date = current_calendar.get('end_date')
            if date is not None:
                # Set the last hour of the date if existing
                date = datetime.datetime.combine(date, datetime.time(23, 59))
            end_date_field_name = f'{base_field_name}_end_date'
            setattr(admission, end_date_field_name, date)
            field_questions_to_display.append(end_date_field_name)

            academic_year_field_name = f'{base_field_name}_academic_year'
            setattr(admission, academic_year_field_name, current_calendar.get('academic_year'))
            field_questions_to_display.append(academic_year_field_name)

        # Build relevant field list
        if self.get_permission_object().training.acronym in SIGLES_WITH_QUOTA:
            field_questions_to_display.append('is_non_resident')
        if admission.reorientation_pool_end_date is not None:
            field_questions_to_display += [
                'is_belgian_bachelor',
                'is_external_reorientation',
                'regular_registration_proof',
                'reorientation_form',
            ]
        elif admission.modification_pool_end_date is not None:
            field_questions_to_display += [
                'is_belgian_bachelor',
                'is_external_modification',
                'registration_change_form',
                'regular_registration_proof_for_registration_change',
            ]

        class DynamicPoolQuestionsSerializer(PoolQuestionsSerializer):
            class Meta:
                model = GeneralEducationAdmission
                fields = field_questions_to_display

        serializer = DynamicPoolQuestionsSerializer(instance=admission)
        return Response(serializer.data)

    @extend_schema(operation_id='update_pool_questions')
    def put(self, request, *args, **kwargs):
        """Update pool questions"""
        admission = GeneralEducationAdmission.objects.get(uuid=kwargs.get('uuid'))
        data = {
            # Reset to default if not defined
            'is_non_resident': None,
            'is_belgian_bachelor': None,
            'is_external_modification': None,
            'is_external_reorientation': None,
            'registration_change_form': [],
            'regular_registration_proof_for_registration_change': [],
            'regular_registration_proof': [],
            'reorientation_form': [],
            # Add user input
            **request.data,
        }
        serializer = PoolQuestionsSerializer(instance=admission, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.get_permission_object().update_detailed_status(request.user.person)
        return Response(serializer.data, status=status.HTTP_200_OK)
