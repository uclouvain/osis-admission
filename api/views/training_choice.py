# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.permissions import (
    IsListingOrHasNotAlreadyCreatedForGeneralEducationPermission,
    IsListingOrHasNotAlreadyCreatedForContinuingEducationPermission,
)
from admission.api.schema import ResponseSpecificSchema
from admission.ddd.admission.formation_generale.commands import (
    InitierPropositionCommand as InitierPropositionGeneraleCommand,
)
from admission.ddd.admission.formation_continue.commands import (
    InitierPropositionCommand as InitierPropositionContinueCommand,
)
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class GeneralTrainingChoiceSchema(ResponseSpecificSchema):
    operation_id_base = '_general_training_choice'
    serializer_mapping = {
        'POST': (
            serializers.InitierPropositionGeneraleCommandSerializer,
            serializers.PropositionIdentityDTOSerializer,
        ),
    }


class GeneralTrainingChoiceAPIView(
    APIPermissionRequiredMixin,
    CreateAPIView,
):
    name = "general_training_choice"
    schema = GeneralTrainingChoiceSchema()
    permission_classes = [IsListingOrHasNotAlreadyCreatedForGeneralEducationPermission]

    def post(self, request, *args, **kwargs):
        serializer = serializers.InitierPropositionGeneraleCommandSerializer(data=request.data)
        serializer.is_valid(True)
        result = message_bus_instance.invoke(
            InitierPropositionGeneraleCommand(
                **serializer.data,
            )
        )
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ContinuingTrainingChoiceSchema(ResponseSpecificSchema):
    operation_id_base = '_continuing_training_choice'
    serializer_mapping = {
        'POST': (
            serializers.InitierPropositionContinueCommandSerializer,
            serializers.PropositionIdentityDTOSerializer,
        ),
    }


class ContinuingTrainingChoiceAPIView(
    APIPermissionRequiredMixin,
    CreateAPIView,
):
    name = "continuing_training_choice"
    schema = ContinuingTrainingChoiceSchema()
    permission_classes = [IsListingOrHasNotAlreadyCreatedForContinuingEducationPermission]

    def post(self, request, *args, **kwargs):
        serializer = serializers.InitierPropositionContinueCommandSerializer(data=request.data)
        serializer.is_valid(True)
        result = message_bus_instance.invoke(
            InitierPropositionContinueCommand(
                **serializer.data,
            )
        )
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
