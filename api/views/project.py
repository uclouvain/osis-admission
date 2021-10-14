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

from admission.api.schema import ResponseSpecificSchema
from admission.contrib import serializers
from backoffice.settings.rest_framework.common_views import DisplayExceptionsByFieldNameAPIMixin
from admission.ddd.preparation.projet_doctoral.commands import (
    CompleterPropositionCommand, GetPropositionCommand,
    InitierPropositionCommand,
    SearchPropositionsCommand,
)
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (
    BureauCDEInconsistantException,
    ContratTravailInconsistantException,
    InstitutionInconsistanteException,
    JustificationRequiseException,
)
from infrastructure.messages_bus import message_bus_instance


class PropositionListSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.PropositionSearchDTOSerializer,
        'POST': (serializers.InitierPropositionCommandSerializer, serializers.PropositionIdentityDTOSerializer),
    }

    def get_operation_id_base(self, path, method, action):
        return '_proposition' if method == 'POST' else '_propositions'


class PropositionListView(DisplayExceptionsByFieldNameAPIMixin, ListCreateAPIView):
    schema = PropositionListSchema()
    pagination_class = None
    filter_backends = []
    field_name_by_exception = {
        JustificationRequiseException: ['justification'],
        InstitutionInconsistanteException: ['institution'],
        ContratTravailInconsistantException: ['type_contrat_travail'],
        BureauCDEInconsistantException: ['bureau_CDE'],
    }

    def list(self, request, **kwargs):
        """List the propositions of the logged in user"""
        proposition_list = message_bus_instance.invoke(
            SearchPropositionsCommand(matricule_candidat=request.user.person.global_id)
        )
        serializer = serializers.PropositionSearchDTOSerializer(instance=proposition_list, many=True)
        return Response(serializer.data)

    def create(self, request, **kwargs):
        """Create a new proposition"""
        serializer = serializers.InitierPropositionCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(InitierPropositionCommand(**serializer.data))
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PropositionSchema(ResponseSpecificSchema):
    operation_id_base = '_proposition'
    serializer_mapping = {
        'GET': serializers.PropositionDTOSerializer,
        'PUT': (serializers.CompleterPropositionCommandSerializer, serializers.PropositionIdentityDTOSerializer),
    }


class PropositionViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericAPIView):
    schema = PropositionSchema()
    pagination_class = None
    filter_backends = []

    def get(self, request, *args, **kwargs):
        """Get a single proposition"""
        # TODO call osis_role perm for this object
        proposition = message_bus_instance.invoke(
            GetPropositionCommand(uuid_proposition=kwargs.get('uuid'))
        )
        serializer = serializers.PropositionDTOSerializer(instance=proposition)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """Edit a proposition"""
        serializer = serializers.CompleterPropositionCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(CompleterPropositionCommand(**serializer.data))
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)
