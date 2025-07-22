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
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.permissions import IsListingOrHasNotAlreadyCreatedPermission
from admission.api.serializers.training_choice import SpecificEnrolmentPeriodsSerializer
from admission.ddd.admission.doctorat.preparation import (
    commands as doctorate_education_commands,
)
from admission.ddd.admission.formation_continue import (
    commands as continuing_education_commands,
)
from admission.ddd.admission.formation_generale import (
    commands as general_education_commands,
)
from admission.ddd.admission.formation_generale.commands import (
    RecupererPeriodeInscriptionSpecifiqueBachelierMedecineDentisterieQuery,
)
from admission.utils import (
    get_cached_admission_perm_obj,
    get_cached_continuing_education_admission_perm_obj,
    get_cached_general_education_admission_perm_obj,
)
from backoffice.settings.rest_framework.common_views import (
    DisplayExceptionsByFieldNameAPIMixin,
)
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


@extend_schema_view(
    get=extend_schema(operation_id='retrieveSpecificEnrolmentPeriods'),
)
class SpecificEnrolmentPeriodsApiView(APIPermissionRequiredMixin, RetrieveAPIView):
    name = "specific_enrolment_periods"
    permission_classes = [IsListingOrHasNotAlreadyCreatedPermission]
    serializer_class = SpecificEnrolmentPeriodsSerializer
    pagination_class = None
    filter_backends = []

    def get_object(self):
        return {
            'medicine_dentistry_bachelor': message_bus_instance.invoke(
                RecupererPeriodeInscriptionSpecifiqueBachelierMedecineDentisterieQuery(),
            ),
        }


class GeneralTrainingChoiceAPIView(
    APIPermissionRequiredMixin,
    CreateAPIView,
):
    name = "general_training_choice"
    permission_classes = [IsListingOrHasNotAlreadyCreatedPermission]

    @extend_schema(
        request=serializers.InitierPropositionGeneraleCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='create_general_training_choice',
    )
    def post(self, request, *args, **kwargs):
        serializer = serializers.InitierPropositionGeneraleCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(
            general_education_commands.InitierPropositionCommand(
                **serializer.data,
            )
        )
        get_cached_general_education_admission_perm_obj(result.uuid).update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ContinuingTrainingChoiceAPIView(
    APIPermissionRequiredMixin,
    CreateAPIView,
):
    name = "continuing_training_choice"
    permission_classes = [IsListingOrHasNotAlreadyCreatedPermission]

    @extend_schema(
        request=serializers.InitierPropositionContinueCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='create_continuing_training_choice',
    )
    def post(self, request, *args, **kwargs):
        serializer = serializers.InitierPropositionContinueCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(
            continuing_education_commands.InitierPropositionCommand(
                **serializer.data,
            )
        )
        get_cached_continuing_education_admission_perm_obj(result.uuid).update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DoctorateTrainingChoiceAPIView(
    APIPermissionRequiredMixin,
    DisplayExceptionsByFieldNameAPIMixin,
    CreateAPIView,
):
    name = "doctorate_training_choice"
    permission_classes = [IsListingOrHasNotAlreadyCreatedPermission]

    @extend_schema(
        request=serializers.InitierPropositionCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='create_doctorate_training_choice',
    )
    def post(self, request, *args, **kwargs):
        serializer = serializers.InitierPropositionCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(doctorate_education_commands.InitierPropositionCommand(**serializer.data))
        get_cached_admission_perm_obj(result.uuid).update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GeneralUpdateTrainingChoiceAPIView(
    APIPermissionRequiredMixin,
    UpdateAPIView,
):
    name = "general_training_choice"
    permission_classes = [IsListingOrHasNotAlreadyCreatedPermission]
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission_training_choice',
        'PUT': 'admission.change_generaleducationadmission_training_choice',
    }
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.PropositionIdentityDTOSerializer

    @extend_schema(
        responses=None,
        operation_id='list_general_training_choices',
    )
    def get(self, request, *args, **kwargs):
        """
        This method is only used to check the permission.
        We have to return some data as the schema expects a 200 status and the deserializer expects some data.
        """
        return Response(data=[])

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])

    @extend_schema(
        request=serializers.ModifierChoixFormationGeneraleCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='update_general_training_choice',
    )
    def put(self, request, *args, **kwargs):
        serializer = serializers.ModifierChoixFormationGeneraleCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(
            general_education_commands.ModifierChoixFormationCommand(
                **serializer.data,
            )
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DoctorateUpdateAdmissionTypeAPIView(
    APIPermissionRequiredMixin,
    UpdateAPIView,
):
    name = "doctorate_admission_type_update"
    permission_mapping = {
        'GET': 'admission.api_view_admission_training_choice',
        'PUT': 'admission.api_change_admission_training_choice',
    }
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.PropositionIdentityDTOSerializer

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    @extend_schema(
        request=serializers.ModifierTypeAdmissionDoctoraleCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='update_doctorate_training_choice',
    )
    def put(self, request, *args, **kwargs):
        serializer = serializers.ModifierTypeAdmissionDoctoraleCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(
            doctorate_education_commands.ModifierTypeAdmissionCommand(
                **serializer.data,
            )
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ContinuingUpdateTrainingChoiceAPIView(
    APIPermissionRequiredMixin,
    UpdateAPIView,
):
    name = "continuing_training_choice"
    permission_mapping = {
        'GET': 'admission.view_continuingeducationadmission_training_choice',
        'PUT': 'admission.change_continuingeducationadmission_training_choice',
    }
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.PropositionIdentityDTOSerializer

    @extend_schema(responses=None, operation_id='list_continuing_training_choices')
    def get(self, request, *args, **kwargs):
        """
        This method is only used to check the permission.
        We have to return some data as the schema expects a 200 status and the deserializer expects some data.
        """
        return Response(data=[])

    def get_permission_object(self):
        return get_cached_continuing_education_admission_perm_obj(self.kwargs['uuid'])

    @extend_schema(
        request=serializers.ModifierChoixFormationContinueCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='update_continuing_training_choice',
    )
    def put(self, request, *args, **kwargs):
        serializer = serializers.ModifierChoixFormationContinueCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(
            continuing_education_commands.ModifierChoixFormationCommand(
                **serializer.data,
            )
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)
