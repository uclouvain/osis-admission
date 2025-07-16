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
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.ddd.admission.doctorat.preparation.commands import (
    DesignerPromoteurReferenceCommand,
    GetGroupeDeSupervisionCommand,
    IdentifierMembreCACommand,
    IdentifierPromoteurCommand,
    ModifierMembreSupervisionExterneCommand,
    SoumettreCACommand,
    SupprimerMembreCACommand,
    SupprimerPromoteurCommand,
)
from admission.models.enums.actor_type import ActorType
from admission.utils import get_cached_admission_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    "SupervisionAPIView",
    "SupervisionSetReferencePromoterAPIView",
    "SupervisionSubmitCaAPIView",
]


class SupervisionAPIView(
    APIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    GenericAPIView,
):
    name = "supervision"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.api_view_admission_supervision',
        'PUT': 'admission.api_add_supervision_member',
        'POST': 'admission.api_remove_supervision_member',
        'PATCH': 'admission.api_edit_external_supervision_member',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    @extend_schema(
        responses=serializers.SupervisionDTOSerializer,
        operation_id='retrieve_supervision',
    )
    def get(self, request, *args, **kwargs):
        """Get the supervision group of a proposition"""
        supervision = message_bus_instance.invoke(GetGroupeDeSupervisionCommand(uuid_proposition=kwargs.get('uuid')))
        serializer = serializers.SupervisionDTOSerializer(instance=supervision)
        return Response(serializer.data)

    @extend_schema(
        request=serializers.IdentifierSupervisionActorSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='add_member',
    )
    def put(self, request, *args, **kwargs):
        """Add a supervision group member for a proposition"""
        data = {
            'uuid_proposition': str(self.kwargs['uuid']),
            'matricule_auteur': self.get_permission_object().candidate.global_id,
            **request.data,
        }
        serializers.IdentifierSupervisionActorSerializer(data=data).is_valid(raise_exception=True)
        if data.pop('actor_type') == ActorType.CA_MEMBER.name:
            serializer_cls = serializers.IdentifierMembreCACommandSerializer
            cmd = IdentifierMembreCACommand
        else:
            serializer_cls = serializers.IdentifierPromoteurCommandSerializer
            cmd = IdentifierPromoteurCommand

        serializer_cls(data=data).is_valid(raise_exception=True)
        result = message_bus_instance.invoke(cmd(**data))
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=serializers.SupervisionActorReferenceSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='remove_member',
    )
    def post(self, request, *args, **kwargs):
        """Remove a supervision group member for a proposition"""
        serializers.SupervisionActorReferenceSerializer(data=request.data).is_valid(raise_exception=True)
        data = {
            'uuid_proposition': str(self.kwargs['uuid']),
            'matricule_auteur': self.get_permission_object().candidate.global_id,
        }
        if request.data['actor_type'] == ActorType.CA_MEMBER.name:
            serializer_cls = serializers.SupprimerMembreCACommandSerializer
            data['uuid_membre_ca'] = request.data['uuid_membre']
            cmd = SupprimerMembreCACommand
        else:
            serializer_cls = serializers.SupprimerPromoteurCommandSerializer
            data['uuid_promoteur'] = request.data['uuid_membre']
            cmd = SupprimerPromoteurCommand

        serializer_cls(data=data).is_valid(raise_exception=True)
        result = message_bus_instance.invoke(cmd(**data))
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=serializers.ModifierMembreSupervisionExterneSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='edit_external_member',
    )
    def patch(self, request, *args, **kwargs):
        """Edit an external supervision group member for a proposition"""
        serializers.ModifierMembreSupervisionExterneSerializer(data=request.data).is_valid(raise_exception=True)
        result = message_bus_instance.invoke(
            ModifierMembreSupervisionExterneCommand(
                matricule_auteur=self.get_permission_object().candidate.global_id,
                **request.data,
            )
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SupervisionSetReferencePromoterAPIView(APIPermissionRequiredMixin, GenericAPIView):
    name = "set-reference-promoter"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'PUT': 'admission.api_set_reference_promoter',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    @extend_schema(
        request=serializers.DesignerPromoteurReferenceCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='set_reference_promoter',
    )
    def put(self, request, *args, **kwargs):
        """Set a supervision group member as reference promoter"""
        serializers.DesignerPromoteurReferenceCommandSerializer(data=request.data).is_valid(raise_exception=True)
        result = message_bus_instance.invoke(
            DesignerPromoteurReferenceCommand(
                matricule_auteur=self.get_permission_object().candidate.global_id,
                **request.data,
            )
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SupervisionSubmitCaAPIView(APIPermissionRequiredMixin, GenericAPIView):
    name = "submit-ca"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'POST': 'admission.api_submit_ca',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    @extend_schema(
        request=None,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='submit_ca',
    )
    def post(self, request, *args, **kwargs):
        """Submit the new CA"""
        result = message_bus_instance.invoke(
            SoumettreCACommand(
                uuid_proposition=str(self.kwargs['uuid']),
            )
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)
