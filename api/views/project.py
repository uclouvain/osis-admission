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
from django.db.models import Prefetch
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.permissions import IsListingOrHasNotAlreadyCreatedPermission, IsSupervisionMember
from admission.api.schema import ResponseSpecificSchema
from admission.contrib.models import DoctorateAdmission
from admission.ddd.admission.doctorat.preparation.commands import (
    CompleterPropositionCommand,
    GetPropositionCommand,
    ListerPropositionsCandidatQuery as ListerPropositionsDoctoralesCandidatQuery,
    ListerPropositionsSuperviseesQuery,
    SupprimerPropositionCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import JustificationRequiseException
from admission.ddd.admission.formation_continue.commands import (
    ListerPropositionsCandidatQuery as ListerPropositionsFormationContinueCandidatQuery,
)
from admission.ddd.admission.formation_generale.commands import (
    ListerPropositionsCandidatQuery as ListerPropositionsFormationGeneraleCandidatQuery,
)
from admission.utils import get_cached_admission_perm_obj
from backoffice.settings.rest_framework.common_views import DisplayExceptionsByFieldNameAPIMixin
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin
from osis_signature.models import Actor

__all__ = [
    "PropositionListView",
    "SupervisedPropositionListView",
    "PropositionViewSet",
]


class PropositionListSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.PropositionSearchSerializer,
    }
    # Force schema to return an object (so that we have the results and the links)
    list_force_object = True

    def get_operation_id_base(self, path, method, action):
        return '_proposition' if method == 'POST' else '_propositions'


class PropositionListView(APIPermissionRequiredMixin, DisplayExceptionsByFieldNameAPIMixin, ListCreateAPIView):
    name = "propositions"
    schema = PropositionListSchema()
    pagination_class = None
    filter_backends = []
    permission_classes = [IsListingOrHasNotAlreadyCreatedPermission]

    field_name_by_exception = {
        JustificationRequiseException: ['justification'],
    }

    def list(self, request, **kwargs):
        """List the propositions of the logged in user"""
        candidate_global_id = request.user.person.global_id

        doctorate_list, general_education_list, continuing_education_list = message_bus_instance.invoke_multiple(
            [
                ListerPropositionsDoctoralesCandidatQuery(matricule_candidat=candidate_global_id),
                ListerPropositionsFormationGeneraleCandidatQuery(matricule_candidat=candidate_global_id),
                ListerPropositionsFormationContinueCandidatQuery(matricule_candidat=candidate_global_id),
            ]
        )

        serializer = serializers.PropositionSearchSerializer(
            instance={
                "doctorate_propositions": doctorate_list,
                "general_education_propositions": general_education_list,
                "continuing_education_propositions": continuing_education_list,
            },
            context=self.get_serializer_context(),
        )

        return Response(serializer.data)

    def create(self, request, **kwargs):
        """Not implemented"""
        # Only used to know if the creation is possible whatever the context
        raise NotImplementedError


class SupervisedPropositionListSchema(ResponseSpecificSchema):
    operation_id_base = '_supervised_propositions'
    serializer_mapping = {
        'GET': serializers.DoctoratePropositionSearchDTOSerializer,
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
        # Add a _perm_obj to each instance to optimize permission check performance
        queryset = (
            DoctorateAdmission.objects.select_related(
                'supervision_group',
                'candidate',
                'training__management_entity__admission_config',
            )
            .prefetch_related(
                Prefetch('supervision_group__actors', Actor.objects.select_related('supervisionactor').all())
            )
            .filter(uuid__in=[p.uuid for p in proposition_list])
            .in_bulk(field_name='uuid')
        )
        for proposition in proposition_list:
            proposition._perm_obj = queryset[proposition.uuid]
        serializer = serializers.DoctoratePropositionSearchDTOSerializer(
            instance=proposition_list,
            context=self.get_serializer_context(),
            many=True,
        )
        return Response(serializer.data)


class PropositionSchema(ResponseSpecificSchema):
    operation_id_base = '_proposition'
    serializer_mapping = {
        'GET': serializers.DoctoratePropositionDTOSerializer,
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
            return serializers.PROPOSITION_ERROR_SCHEMA
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
        serializer = serializers.DoctoratePropositionDTOSerializer(
            instance=proposition,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """Edit a proposition"""
        serializer = serializers.CompleterPropositionCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(CompleterPropositionCommand(**serializer.data))
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """Soft-Delete a proposition"""
        proposition_id = message_bus_instance.invoke(
            SupprimerPropositionCommand(uuid_proposition=kwargs.get('uuid')),
        )
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)
