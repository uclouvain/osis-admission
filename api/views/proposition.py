# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.schema import ResponseSpecificSchema
from admission.ddd.admission.formation_generale.commands import (
    RecupererPropositionQuery as RecupererPropositionFormationGeneraleQuery,
)
from admission.ddd.admission.formation_continue.commands import (
    RecupererPropositionQuery as RecupererPropositionFormationContinueQuery,
)
from admission.utils import get_cached_general_education_admission_perm_obj, \
    get_cached_continuing_education_admission_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class GeneralPropositionSchema(ResponseSpecificSchema):
    operation_id_base = '_general_education_proposition'
    serializer_mapping = {
        'GET': serializers.GeneralEducationPropositionDTOSerializer,
    }


class GeneralPropositionViewSet(APIPermissionRequiredMixin, RetrieveAPIView):
    name = "general_propositions"
    schema = GeneralPropositionSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission',
    }

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get a single proposition"""
        proposition = message_bus_instance.invoke(
            RecupererPropositionFormationGeneraleQuery(uuid_proposition=kwargs.get('uuid')),
        )
        serializer = serializers.GeneralEducationPropositionDTOSerializer(
            instance=proposition,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)


class ContinuingPropositionSchema(ResponseSpecificSchema):
    operation_id_base = '_continuing_education_proposition'
    serializer_mapping = {
        'GET': serializers.ContinuingEducationPropositionDTOSerializer,
    }


class ContinuingPropositionViewSet(APIPermissionRequiredMixin, RetrieveAPIView):
    name = "continuing_propositions"
    schema = ContinuingPropositionSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_continuingeducationadmission',
    }

    def get_permission_object(self):
        return get_cached_continuing_education_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get a single proposition"""
        proposition = message_bus_instance.invoke(
            RecupererPropositionFormationContinueQuery(uuid_proposition=kwargs.get('uuid')),
        )
        serializer = serializers.ContinuingEducationPropositionDTOSerializer(
            instance=proposition,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)
