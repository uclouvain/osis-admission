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
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admission.api import serializers
from admission.ddd.admission.doctorat.preparation.commands import (
    DemanderSignaturesCommand,
    RenvoyerInvitationSignatureExterneCommand,
)
from admission.utils import get_cached_admission_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class RequestSignaturesAPIView(APIPermissionRequiredMixin, APIView):
    name = "request-signatures"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'PUT': 'admission.api_resend_external_invitation',
        'POST': 'admission.api_request_signatures',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    @extend_schema(
        request=serializers.RenvoyerInvitationSignatureExterneSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='update_signatures',
    )
    def put(self, request, *args, **kwargs):
        """Resend an invitation for and external member."""
        serializer = serializers.RenvoyerInvitationSignatureExterneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(
            RenvoyerInvitationSignatureExterneCommand(uuid_proposition=str(kwargs["uuid"]), **serializer.data)
        )
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=None,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='create_signatures',
    )
    def post(self, request, *args, **kwargs):
        """Ask for all promoters and members to sign the proposition."""
        result = message_bus_instance.invoke(
            DemanderSignaturesCommand(
                matricule_auteur=self.get_permission_object().candidate.global_id,
                uuid_proposition=str(kwargs["uuid"]),
            )
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
