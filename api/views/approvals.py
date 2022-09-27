# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admission.api import serializers
from admission.api.schema import ResponseSpecificSchema
from admission.ddd.admission.projet_doctoral.preparation.commands import (
    ApprouverPropositionCommand,
    ApprouverPropositionParPdfCommand,
    RefuserPropositionCommand,
)
from admission.utils import get_cached_admission_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class ApprovePropositionSchema(ResponseSpecificSchema):
    method_mapping = {
        'post': 'approve',
        'put': 'reject',
    }

    operation_id_base = "_proposition"
    serializer_mapping = {
        "POST": (serializers.ApprouverPropositionCommandSerializer, serializers.PropositionIdentityDTOSerializer),
        "PUT": (serializers.RefuserPropositionCommandSerializer, serializers.PropositionIdentityDTOSerializer),
    }


class ApprovePropositionAPIView(APIPermissionRequiredMixin, APIView):
    name = "approvals"
    schema = ApprovePropositionSchema()
    permission_mapping = {
        'POST': 'admission.approve_proposition',
        'PUT': 'admission.approve_proposition',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def post(self, request, *args, **kwargs):
        """Approve the proposition."""
        serializer = serializers.ApprouverPropositionCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        proposition_id = message_bus_instance.invoke(
            ApprouverPropositionCommand(
                uuid_proposition=str(kwargs["uuid"]),
                **serializer.data,
            ),
        )
        self.get_permission_object().update_detailed_status()

        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        """Reject the proposition."""
        serializer = serializers.RefuserPropositionCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        proposition_id = message_bus_instance.invoke(
            RefuserPropositionCommand(
                uuid_proposition=str(kwargs["uuid"]),
                **serializer.data,
            ),
        )
        self.get_permission_object().update_detailed_status()

        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApproveByPdfPropositionSchema(ResponseSpecificSchema):
    serializer_mapping = {
        "POST": (serializers.ApprouverPropositionParPdfCommandSerializer, serializers.PropositionIdentityDTOSerializer),
    }

    def get_operation_id(self, path, method):
        return 'approve_by_pdf'


class ApproveByPdfPropositionAPIView(APIPermissionRequiredMixin, APIView):
    name = "approve-by-pdf"
    schema = ApproveByPdfPropositionSchema()
    permission_mapping = {
        'POST': 'admission.approve_proposition_by_pdf',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def post(self, request, *args, **kwargs):
        """Approve the proposition with a pdf file."""
        serializer = serializers.ApprouverPropositionParPdfCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        proposition_id = message_bus_instance.invoke(
            ApprouverPropositionParPdfCommand(
                uuid_proposition=str(kwargs["uuid"]),
                **serializer.data,
            ),
        )
        self.get_permission_object().update_detailed_status()

        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)
