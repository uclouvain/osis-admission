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
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework.settings import api_settings

from admission.api import serializers
from admission.api.permissions import IsListingOrHasNotAlreadyCreatedPermission, IsSupervisionMember
from admission.api.schema import ResponseSpecificSchema
from admission.contrib.models import DoctorateAdmission
from admission.ddd.projet_doctoral.preparation.commands import (
    CompleterPropositionCommand,
    GetPropositionCommand,
    InitierPropositionCommand,
    ListerPropositionsCandidatQuery,
    ListerPropositionsSuperviseesQuery,
    SoumettrePropositionCommand,
    SupprimerPropositionCommand,
    VerifierProjetCommand,
    VerifierPropositionCommand,
)
from admission.ddd.projet_doctoral.preparation.domain.validator.exceptions import (
    CommissionProximiteInconsistantException,
    ContratTravailInconsistantException,
    DomaineTheseInconsistantException,
    InstitutionInconsistanteException,
    JustificationRequiseException,
)
from admission.ddd.projet_doctoral.validation.commands import ApprouverDemandeCddCommand
from admission.utils import gather_business_exceptions, get_cached_admission_perm_obj
from backoffice.settings.rest_framework.common_views import DisplayExceptionsByFieldNameAPIMixin
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    "PropositionListView",
    "SupervisedPropositionListView",
    "PropositionViewSet",
    "VerifyProjectView",
    "SubmitPropositionViewSet",
]


class PropositionListSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.PropositionSearchSerializer,
        'POST': (serializers.InitierPropositionCommandSerializer, serializers.PropositionIdentityDTOSerializer),
    }
    # Force schema to return an object (so that we have the results and the links)
    list_force_object = True

    def get_operation_id_base(self, path, method, action):
        return '_proposition' if method == 'POST' else '_propositions'

    def map_choicefield(self, field):
        schema = super().map_choicefield(field)
        if field.field_name == "commission_proximite":
            self.enums["ChoixCommissionProximite"] = schema
            return {'$ref': "#/components/schemas/ChoixCommissionProximite"}
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
        DomaineTheseInconsistantException: ['domaine_these'],
        ContratTravailInconsistantException: ['type_contrat_travail'],
        CommissionProximiteInconsistantException: ['commission_proximite'],
    }

    def list(self, request, **kwargs):
        """List the propositions of the logged in user"""
        proposition_list = message_bus_instance.invoke(
            ListerPropositionsCandidatQuery(matricule_candidat=request.user.person.global_id),
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
        DoctorateAdmission.objects.get(uuid=result.uuid).update_detailed_status()
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupervisedPropositionListSchema(ResponseSpecificSchema):
    operation_id_base = '_supervised_propositions'
    serializer_mapping = {
        'GET': serializers.PropositionSearchDTOSerializer,
    }


class SupervisedPropositionListView(APIPermissionRequiredMixin, ListAPIView):
    name = "supervised_propositions"
    schema = SupervisedPropositionListSchema(tags=['propositions'])
    pagination_class = None
    filter_backends = []
    permission_classes = [IsSupervisionMember]

    def list(self, request, **kwargs):
        """List the propositions of the supervision group member"""
        proposition_list = message_bus_instance.invoke(
            ListerPropositionsSuperviseesQuery(matricule_membre=request.user.person.global_id),
        )
        serializer = serializers.PropositionSearchDTOSerializer(
            instance=proposition_list,
            context=self.get_serializer_context(),
            many=True,
        )
        return Response(serializer.data)


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
            return {'$ref': "#/components/schemas/ChoixCommissionProximite"}
        return schema

    def map_field(self, field):
        if field.field_name == 'erreurs':
            return {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "status_code": {"type": "string"},
                        "detail": {"type": "string"},
                    },
                },
            }

        return super().map_field(field)


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
            GetPropositionCommand(uuid_proposition=kwargs.get('uuid')),
        )
        serializer = serializers.PropositionDTOSerializer(
            instance=proposition,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """Edit a proposition"""
        serializer = serializers.CompleterPropositionCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(CompleterPropositionCommand(**serializer.data))
        self.get_permission_object().update_detailed_status()
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """Soft-Delete a proposition"""
        proposition_id = message_bus_instance.invoke(
            SupprimerPropositionCommand(uuid_proposition=kwargs.get('uuid')),
        )
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VerifySchema(ResponseSpecificSchema):
    response_description = "Verification errors"

    def get_responses(self, path, method):
        return (
            {
                status.HTTP_200_OK: {
                    "description": self.response_description,
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
                                        },
                                    },
                                },
                            }
                        }
                    },
                }
            }
            if method == 'GET'
            else super(VerifySchema, self).get_responses(path, method)
        )


class VerifyProjectSchema(VerifySchema):
    operation_id_base = '_verify_project'
    response_description = "Project verification errors"


class VerifyProjectView(APIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "verify-project"
    schema = VerifyProjectSchema()
    permission_mapping = {
        'GET': 'admission.change_doctorateadmission_project',
    }
    pagination_class = None
    filter_backends = []

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Check the project to be OK with all validators."""
        data = gather_business_exceptions(VerifierProjetCommand(uuid_proposition=str(kwargs["uuid"])))
        return Response(data.get(api_settings.NON_FIELD_ERRORS_KEY, []), status=status.HTTP_200_OK)


class VerifyPropositionSchema(VerifySchema):
    response_description = "Proposition verification errors"

    serializer_mapping = {
        'POST': serializers.PropositionIdentityDTOSerializer,
    }

    def get_operation_id(self, path, method):
        if method == 'GET':
            return 'verify_proposition'
        elif method == 'POST':
            return 'submit_proposition'
        return super().get_operation_id(path, method)


class SubmitPropositionViewSet(APIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "submit-proposition"
    schema = VerifyPropositionSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.submit_doctorateadmission',
        'POST': 'admission.submit_doctorateadmission',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Check the proposition to be OK with all validators."""
        data = gather_business_exceptions(VerifierPropositionCommand(uuid_proposition=str(kwargs["uuid"])))
        return Response(data.get(api_settings.NON_FIELD_ERRORS_KEY, []), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Submit the proposition."""
        # Trigger the submit command
        proposition_id = message_bus_instance.invoke(SoumettrePropositionCommand(uuid_proposition=str(kwargs["uuid"])))
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        # TODO To remove when the admission approval by CDD and SIC will be created
        message_bus_instance.invoke(ApprouverDemandeCddCommand(uuid=str(kwargs["uuid"])))
        return Response(serializer.data, status=status.HTTP_200_OK)
