# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework import status, mixins
from rest_framework.generics import RetrieveAPIView, GenericAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.schema import ResponseSpecificSchema
from admission.ddd.admission.doctorat.preparation import commands as doctorate_commands
from admission.ddd.admission.formation_continue import commands as continuing_education_commands
from admission.ddd.admission.formation_generale import commands as general_education_commands
from admission.utils import (
    get_cached_general_education_admission_perm_obj,
    get_cached_continuing_education_admission_perm_obj,
    get_cached_admission_perm_obj,
)
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class GeneralPropositionSchema(ResponseSpecificSchema):
    operation_id_base = '_general_education_proposition'
    serializer_mapping = {
        'GET': serializers.GeneralEducationPropositionDTOSerializer,
        'DELETE': serializers.PropositionIdentityDTOSerializer,
    }


class GeneralPropositionView(APIPermissionRequiredMixin, RetrieveAPIView):
    name = "general_propositions"
    schema = GeneralPropositionSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission',
        'DELETE': 'admission.delete_generaleducationadmission',
    }

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get a single proposition"""
        proposition = message_bus_instance.invoke(
            general_education_commands.RecupererPropositionQuery(uuid_proposition=kwargs.get('uuid')),
        )
        serializer = serializers.GeneralEducationPropositionDTOSerializer(
            instance=proposition,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        """Soft-Delete a proposition"""
        proposition_id = message_bus_instance.invoke(
            general_education_commands.SupprimerPropositionCommand(uuid_proposition=kwargs.get('uuid')),
        )
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ContinuingPropositionSchema(ResponseSpecificSchema):
    operation_id_base = '_continuing_education_proposition'
    serializer_mapping = {
        'GET': serializers.ContinuingEducationPropositionDTOSerializer,
        'DELETE': serializers.PropositionIdentityDTOSerializer,
    }


class ContinuingPropositionView(APIPermissionRequiredMixin, RetrieveAPIView):
    name = "continuing_propositions"
    schema = ContinuingPropositionSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_continuingeducationadmission',
        'DELETE': 'admission.delete_continuingeducationadmission',
    }

    def get_permission_object(self):
        return get_cached_continuing_education_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get a single proposition"""
        proposition = message_bus_instance.invoke(
            continuing_education_commands.RecupererPropositionQuery(uuid_proposition=kwargs.get('uuid')),
        )
        serializer = serializers.ContinuingEducationPropositionDTOSerializer(
            instance=proposition,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        """Soft-Delete a proposition"""
        proposition_id = message_bus_instance.invoke(
            continuing_education_commands.SupprimerPropositionCommand(uuid_proposition=kwargs.get('uuid')),
        )
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DoctoratePropositionSchema(ResponseSpecificSchema):
    operation_id_base = '_doctorate_proposition'
    serializer_mapping = {
        'GET': serializers.DoctoratePropositionDTOSerializer,
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


class DoctoratePropositionView(
    APIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    name = "doctorate_propositions"
    schema = DoctoratePropositionSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission',
        'DELETE': 'admission.delete_doctorateadmission',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get a single proposition"""
        proposition = message_bus_instance.invoke(
            doctorate_commands.GetPropositionCommand(uuid_proposition=kwargs.get('uuid')),
        )
        serializer = serializers.DoctoratePropositionDTOSerializer(
            instance=proposition,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        """Soft-Delete a proposition"""
        proposition_id = message_bus_instance.invoke(
            doctorate_commands.SupprimerPropositionCommand(uuid_proposition=kwargs.get('uuid')),
        )
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)
