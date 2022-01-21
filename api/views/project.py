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
from collections import defaultdict

from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework.settings import api_settings

from admission.api import serializers
from admission.api.permissions import IsListingOrHasNotAlreadyCreatedPermission
from admission.api.schema import ResponseSpecificSchema
from admission.ddd.preparation.projet_doctoral.commands import (
    CompleterPropositionCommand, GetPropositionCommand,
    InitierPropositionCommand,
    SearchPropositionsCommand,
    SupprimerPropositionCommand,
    VerifierPropositionCommand,
)
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (
    CommissionProximiteInconsistantException,
    ContratTravailInconsistantException,
    InstitutionInconsistanteException,
    JustificationRequiseException,
)
from admission.utils import get_cached_admission_perm_obj
from backoffice.settings.rest_framework.common_views import DisplayExceptionsByFieldNameAPIMixin
from backoffice.settings.rest_framework.exception_handler import get_error_data
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class PropositionListSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.PropositionSearchSerializer,
        'POST': (serializers.InitierPropositionCommandSerializer, serializers.PropositionIdentityDTOSerializer),
    }
    list_force_object = True

    def get_operation_id_base(self, path, method, action):
        return '_proposition' if method == 'POST' else '_propositions'

    def map_choicefield(self, field):
        schema = super().map_choicefield(field)
        if field.field_name == "commission_proximite":
            self.enums["ChoixCommissionProximite"] = schema
            return {
                '$ref': "#/components/schemas/ChoixCommissionProximite"
            }
        return schema


class PropositionListView(APIPermissionRequiredMixin, DisplayExceptionsByFieldNameAPIMixin, ListCreateAPIView):
    name = "propositions"
    schema = PropositionListSchema()
    pagination_class = None
    filter_backends = []
    permission_classes = [IsListingOrHasNotAlreadyCreatedPermission]

    field_name_by_exception = {
        JustificationRequiseException: ['justification'],
        InstitutionInconsistanteException: ['institution'],
        ContratTravailInconsistantException: ['type_contrat_travail'],
        CommissionProximiteInconsistantException: ['commission_proximite'],
    }

    def list(self, request, **kwargs):
        """List the propositions of the logged in user"""
        proposition_list = message_bus_instance.invoke(
            SearchPropositionsCommand(matricule_candidat=request.user.person.global_id)
        )
        serializer = serializers.PropositionSearchSerializer(
            instance={
                "propositions": proposition_list,
            },
            context=self.get_serializer_context(),
        )
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

    def map_choicefield(self, field):
        schema = super().map_choicefield(field)
        if field.field_name == "commission_proximite":
            self.enums["ChoixCommissionProximite"] = schema
            return {
                '$ref': "#/components/schemas/ChoixCommissionProximite"
            }
        return schema


class PropositionViewSet(
    APIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
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
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get a single proposition"""
        proposition = message_bus_instance.invoke(
            GetPropositionCommand(uuid_proposition=kwargs.get('uuid'))
        )
        serializer = serializers.PropositionDTOSerializer(
            instance=proposition,
            context=self.get_serializer_context()
        )
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


class VerifyPropositionSchema(ResponseSpecificSchema):
    operation_id_base = '_verify_proposition'

    def get_responses(self, path, method):
        return {
            status.HTTP_200_OK: {
                "description": "Proposition verification errors",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "status_code": {
                                        "type": "string",
                                    },
                                    "detail": {
                                        "type": "string",
                                    }
                                }
                            }
                        }}
                }
            }
        }


class VerifyPropositionView(APIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "verify-proposition"
    schema = VerifyPropositionSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission_project',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Check the proposition to be OK with all validators."""
        try:
            # Trigger the verification command
            message_bus_instance.invoke(VerifierPropositionCommand(uuid_proposition=str(kwargs["uuid"])))
        except MultipleBusinessExceptions as exc:
            # Gather all errors for output
            data = defaultdict(list)
            for exception in exc.exceptions:
                data = get_error_data(data, exception, {})
            return Response(data.get(api_settings.NON_FIELD_ERRORS_KEY, []), status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)
