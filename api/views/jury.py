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
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.schema import ResponseSpecificSchema
from admission.ddd.parcours_doctoral.jury.commands import (
    RecupererJuryQuery,
    ModifierJuryCommand,
    AjouterMembreCommand,
    ModifierMembreCommand,
    RetirerMembreCommand,
    ModifierRoleMembreCommand,
    RecupererJuryMembreQuery,
)
from admission.utils import get_cached_admission_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    "JuryPreparationAPIView",
    "JuryMembersListAPIView",
    "JuryMemberDetailAPIView",
]


class JuryPreparationSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.JuryDTOSerializer,
        'POST': (serializers.ModifierJuryCommandSerializer, serializers.JuryIdentityDTOSerializer),
    }

    method_mapping = {
        'get': 'retrieve',
        'post': 'update',
    }

    operation_id_base = '_jury_preparation'


class JuryPreparationAPIView(
    APIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    name = "jury-preparation"
    schema = JuryPreparationSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_admission_jury',
        'POST': 'admission.change_admission_jury',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get the Jury of a doctorate"""
        jury = message_bus_instance.invoke(RecupererJuryQuery(uuid_jury=kwargs.get('uuid')))
        serializer = serializers.JuryDTOSerializer(instance=jury)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Update the jury preparation information"""
        serializer = serializers.ModifierJuryCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            ModifierJuryCommand(
                uuid_doctorat=str(self.kwargs['uuid']),
                **serializer.data,
            )
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = serializers.JuryIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class JuryMembersListSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.MembreJuryDTOSerializer,
        'POST': (serializers.AjouterMembreCommandSerializer, serializers.MembreJuryIdentityDTOSerializer),
    }

    method_mapping = {
        'get': 'list',
        'post': 'create',
    }

    operation_id_base = '_jury_members'


class JuryMembersListAPIView(
    APIPermissionRequiredMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericAPIView,
):
    name = "jury-members-list"
    schema = JuryMembersListSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_admission_jury',
        'POST': 'admission.change_admission_jury',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get the members of a jury"""
        jury = message_bus_instance.invoke(RecupererJuryQuery(uuid_jury=kwargs.get('uuid')))
        serializer = serializers.MembreJuryDTOSerializer(instance=jury.membres, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Add a new member to the jury"""
        serializer = serializers.AjouterMembreCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            AjouterMembreCommand(
                uuid_jury=str(self.kwargs['uuid']),
                **serializer.data,
            )
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        return Response({'uuid': result}, status=status.HTTP_201_CREATED)


class JuryMemberDetailSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.MembreJuryDTOSerializer,
        'PUT': (serializers.ModifierMembreCommandSerializer, serializers.JuryIdentityDTOSerializer),
        'PATCH': (serializers.ModifierRoleMembreCommandSerializer, serializers.JuryIdentityDTOSerializer),
        'DELETE': None,
    }

    method_mapping = {
        'get': 'retrieve',
        'put': 'update',
        'patch': 'update_role',
        'delete': 'remove',
    }

    operation_id_base = '_jury_member'


class JuryMemberDetailAPIView(
    APIPermissionRequiredMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericAPIView,
):
    name = "jury-member-detail"
    schema = JuryMemberDetailSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_admission_jury',
        'PUT': 'admission.change_admission_jury',
        'PATCH': 'admission.change_admission_jury',
        'DELETE': 'admission.change_admission_jury',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get the members of a jury"""
        membre = message_bus_instance.invoke(
            RecupererJuryMembreQuery(
                uuid_jury=str(self.kwargs['uuid']),
                uuid_membre=str(self.kwargs['member_uuid']),
            )
        )
        serializer = serializers.MembreJuryDTOSerializer(instance=membre)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """Update a member of the jury"""
        serializer = serializers.ModifierMembreCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            ModifierMembreCommand(
                uuid_jury=str(self.kwargs['uuid']),
                uuid_membre=str(self.kwargs['member_uuid']),
                **serializer.data,
            )
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = serializers.JuryIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        """Update the role of a member of the jury"""
        serializer = serializers.ModifierRoleMembreCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            ModifierRoleMembreCommand(
                uuid_jury=str(self.kwargs['uuid']),
                uuid_membre=str(self.kwargs['member_uuid']),
                **serializer.data,
            )
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = serializers.JuryIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """Remove a member"""
        message_bus_instance.invoke(
            RetirerMembreCommand(
                uuid_jury=str(self.kwargs['uuid']),
                uuid_membre=str(self.kwargs['member_uuid']),
            )
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        return Response(status=status.HTTP_204_NO_CONTENT)
