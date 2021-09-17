# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.serializers import Serializer

from admission.contrib import serializers
from ddd.logic.admission.preparation.projet_doctoral.commands import (
    CompleterPropositionCommand, GetPropositionCommand,
    InitierPropositionCommand,
    SearchPropositionsCommand,
)
from infrastructure.messages_bus import message_bus_instance


class DetailedAutoSchema(AutoSchema):
    def get_request_body(self, path, method):
        if method not in ('PUT', 'PATCH', 'POST'):
            return {}

        self.request_media_types = self.map_parsers(path, method)

        serializer = self.get_serializer(path, method, for_response=False)

        if not isinstance(serializer, Serializer):
            item_schema = {}
        else:
            item_schema = self._get_reference(serializer)

        return {
            'content': {
                ct: {'schema': item_schema}
                for ct in self.request_media_types
            }
        }

    def get_components(self, path, method):
        if method.lower() == 'delete':
            return {}

        components = {}
        for with_response in [True, False]:
            serializer = self.get_serializer(path, method, for_response=with_response)
            if not isinstance(serializer, Serializer):
                return {}
            component_name = self.get_component_name(serializer)
            content = self.map_serializer(serializer)
            components[component_name] = content

        return components

    def get_serializer(self, path, method, for_response=True):
        raise NotImplementedError


class PropositionListSchema(DetailedAutoSchema):
    def get_operation_id_base(self, path, method, action):
        return '_proposition' if method == 'POST' else '_propositions'

    def get_serializer(self, path, method, for_response=True):
        if method == 'POST':
            if for_response:
                return serializers.PropositionIdentityDTOSerializer()
            return serializers.InitierPropositionCommandSerializer()
        return serializers.PropositionSearchDTOSerializer()


class PropositionListViewSet(ListCreateAPIView):
    schema = PropositionListSchema()
    pagination_class = None
    filter_backends = None

    def list(self, request, **kwargs):
        proposition_list = message_bus_instance.invoke(
            SearchPropositionsCommand(matricule_candidat=request.user.person.global_id)
        )
        serializer = serializers.PropositionSearchDTOSerializer(instance=proposition_list, many=True)
        return Response(serializer.data)

    def create(self, request, **kwargs):
        serializer = serializers.InitierPropositionCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(InitierPropositionCommand(**serializer.data))
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PropositionSchema(DetailedAutoSchema):
    def get_operation_id_base(self, path, method, action):
        return '_proposition'

    def get_serializer(self, path, method, for_response=True):
        if method == 'PUT':
            if for_response:
                return serializers.PropositionIdentityDTOSerializer()
            return serializers.CompleterPropositionCommandSerializer()
        return serializers.PropositionDTOSerializer()


class PropositionViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericAPIView):
    schema = PropositionSchema()
    pagination_class = None
    filter_backends = None

    def get(self, request, *args, **kwargs):
        # TODO call osis_role perm for this object
        proposition = message_bus_instance.invoke(
            GetPropositionCommand(uuid_proposition=kwargs.get('uuid'))
        )
        serializer = serializers.PropositionDTOSerializer(instance=proposition)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        serializer = serializers.CompleterPropositionCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(CompleterPropositionCommand(**serializer.data))
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)
