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

from datetime import timedelta

from django.utils.functional import cached_property
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema, extend_schema_view
from osis_signature.utils import get_actor_from_token
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from admission.api import serializers
from admission.ddd.admission.doctorat.preparation.commands import (
    ApprouverPropositionCommand,
    ApprouverPropositionParPdfCommand,
    GetGroupeDeSupervisionCommand,
    GetPropositionCommand,
    RefuserPropositionCommand,
)
from admission.utils import get_cached_admission_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    "ApprovePropositionAPIView",
    "ExternalApprovalPropositionAPIView",
    "ApproveByPdfPropositionAPIView",
]
EXTERNAL_ACTOR_TOKEN_EXPIRATION_DAYS = 15


class ApprovePropositionMixin:
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
        self.get_permission_object().update_detailed_status(getattr(request.user, 'person', None))

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
        self.get_permission_object().update_detailed_status(getattr(request.user, 'person', None))

        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(
        request=serializers.ApprouverPropositionCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='approve_proposition',
    ),
    put=extend_schema(
        request=serializers.RefuserPropositionCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='reject_proposition',
    ),
    get=extend_schema(
        responses=None,
        operation_id='retrieve_doctorate_management',
    ),
)
class ApprovePropositionAPIView(ApprovePropositionMixin, APIPermissionRequiredMixin, APIView):
    name = "approvals"
    permission_mapping = {
        'POST': 'admission.api_approve_proposition',
        'PUT': 'admission.api_approve_proposition',
        'GET': 'admission.api_view_doctorate_management',
    }

    def get(self, request, *args, **kwargs):
        """This method is only used to check the access permission to the doctorate management pages."""
        # We have to return some data as the schema expects a 200 status and the deserializer expects some data.
        return Response(data=[])


@extend_schema_view(
    get=extend_schema(
        responses=serializers.ExternalSupervisionDTOSerializer,
        operation_id='get_external_proposition',
    ),
    post=extend_schema(
        request=serializers.ApprouverPropositionCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='approve_external_proposition',
    ),
    put=extend_schema(
        request=serializers.RefuserPropositionCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='reject_external_proposition',
    ),
)
class ExternalApprovalPropositionAPIView(ApprovePropositionMixin, APIView):
    name = "external-approvals"
    authentication_classes = []
    permission_classes = []

    @cached_property
    def actor(self):
        return get_actor_from_token(self.kwargs['token'])

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        # Load actor from token
        if (
            not self.actor
            # must be part of supervision group
            or self.actor.process_id != self.get_permission_object().supervision_group_id
            # must be not older than 15 days
            or self.actor.states.last().created_at < now() - timedelta(days=EXTERNAL_ACTOR_TOKEN_EXPIRATION_DAYS)
        ):
            raise PermissionDenied
        # Override the request data to use the actor's uuid loaded from token
        request.data['uuid_membre'] = str(self.actor.uuid)

    def get(self, request, *args, **kwargs):
        """Returns necessary info about proposition while checking token."""
        proposition = message_bus_instance.invoke(GetPropositionCommand(uuid_proposition=kwargs.get('uuid')))
        supervision = message_bus_instance.invoke(GetGroupeDeSupervisionCommand(uuid_proposition=kwargs['uuid']))
        serializer = serializers.ExternalSupervisionDTOSerializer(
            instance={
                'proposition': proposition,
                'supervision': supervision,
            },
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApproveByPdfPropositionAPIView(APIPermissionRequiredMixin, APIView):
    name = "approve-by-pdf"
    permission_mapping = {
        'POST': 'admission.api_approve_proposition_by_pdf',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    @extend_schema(
        request=serializers.ApprouverPropositionParPdfCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='approve_by_pdf',
    )
    def post(self, request, *args, **kwargs):
        """Approve the proposition with a pdf file."""
        serializer = serializers.ApprouverPropositionParPdfCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        proposition_id = message_bus_instance.invoke(
            ApprouverPropositionParPdfCommand(
                uuid_proposition=str(kwargs["uuid"]),
                matricule_auteur=self.get_permission_object().candidate.global_id,
                **serializer.data,
            ),
        )
        self.get_permission_object().update_detailed_status(request.user.person)

        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)
