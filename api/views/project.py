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
from rest_framework.generics import GenericAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.response import Response

from admission.api.schema import ResponseSpecificSchema
from admission.api import serializers
from admission.contrib.models.doctorate import DoctorateAdmission
from backoffice.settings.rest_framework.common_views import DisplayExceptionsByFieldNameAPIMixin
from admission.ddd.preparation.projet_doctoral.commands import (
    CompleterPropositionCommand, GetPropositionCommand,
    InitierPropositionCommand,
    SearchPropositionsCommand,
    SupprimerPropositionCommand,
)
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (
    BureauCDEInconsistantException,
    ContratTravailInconsistantException,
    InstitutionInconsistanteException,
    JustificationRequiseException,
)
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class PropositionListSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.PropositionSearchDTOSerializer,
        'POST': (serializers.InitierPropositionCommandSerializer, serializers.PropositionIdentityDTOSerializer),
    }

    def get_operation_id_base(self, path, method, action):
        return '_proposition' if method == 'POST' else '_propositions'


class PropositionListView(APIPermissionRequiredMixin, DisplayExceptionsByFieldNameAPIMixin, ListCreateAPIView):
    name = "propositions"
    schema = PropositionListSchema()
    pagination_class = None
    filter_backends = []
    field_name_by_exception = {
        JustificationRequiseException: ['justification'],
        InstitutionInconsistanteException: ['institution'],
        ContratTravailInconsistantException: ['type_contrat_travail'],
        BureauCDEInconsistantException: ['bureau_CDE'],
    }
    permission_mapping = {
        'POST': 'admission.add_doctorateadmission',
        'GET': 'admission.access_doctorateadmission',
    }

    def list(self, request, **kwargs):
        """List the propositions of the logged in user"""
        proposition_list = message_bus_instance.invoke(
            SearchPropositionsCommand(matricule_candidat=request.user.person.global_id)
        )
        serializer = serializers.PropositionSearchDTOSerializer(
            instance=proposition_list,
            many=True,
            context={
                'request': request,
            },
        )
        print(serializer.data)
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
        'DELETE': serializers.PropositionIdentityDTOSerializer,
    }


class PropositionViewSet(APIPermissionRequiredMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericAPIView):
    name = "propositions"
    schema = PropositionSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission_project',
        'PUT': 'admission.change_doctorateadmission_project',
        'DELETE': 'admission.delete_doctorateadmission',
    }

    def get_permission_object(self):
        return get_object_or_404(DoctorateAdmission, uuid=self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get a single proposition"""
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

    def delete(self, request, *args, **kwargs):
        """Soft-Delete a proposition"""
        proposition_id = message_bus_instance.invoke(
            SupprimerPropositionCommand(uuid_proposition=kwargs.get('uuid'))
        )
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)
