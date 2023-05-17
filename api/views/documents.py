# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List

from rest_framework import generics
from rest_framework.response import Response

from admission.api import serializers
from admission.api.schema import ResponseSpecificSchema
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.formation_generale import commands as general_education_commands
from admission.utils import get_cached_general_education_admission_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class RequestedDocumentsListSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.DocumentSpecificQuestionSerializer,
        'POST': (
            serializers.CompleterEmplacementsDocumentsParCandidatCommandSerializer,
            serializers.PropositionIdentityDTOSerializer,
        ),
    }


class RequestedDocumentListView(APIPermissionRequiredMixin, generics.ListCreateAPIView):
    name = "documents"
    schema = RequestedDocumentsListSchema()
    serializer_class = serializers.DocumentSpecificQuestionSerializer
    pagination_class = None
    filter_backends = []
    get_documents_command = None
    complete_documents_commands = None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['admission'] = self.get_permission_object()
        return context

    def list(self, request, *args, **kwargs):
        requested_documents: List[EmplacementDocumentDTO] = message_bus_instance.invoke(
            self.get_documents_command(
                uuid_proposition=self.kwargs['uuid'],
            )
        )

        serializer = self.get_serializer(requested_documents, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        input_serializer = serializers.CompleterEmplacementsDocumentsParCandidatCommandSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            self.complete_documents_commands(
                uuid_proposition=self.kwargs['uuid'],
                reponses_documents_a_completer=input_serializer.validated_data['reponses_documents_a_completer'],
            )
        )

        output_serializer = serializers.PropositionIdentityDTOSerializer(instance=result)

        return Response(output_serializer.data)


class GeneralRequestedDocumentListView(RequestedDocumentListView):
    name = "general_documents"
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission_documents',
        'POST': 'admission.change_generaleducationadmission_documents',
    }
    schema = RequestedDocumentsListSchema(operation_id_base='_general_documents')

    get_documents_command = general_education_commands.RecupererDocumentsReclamesPropositionQuery
    complete_documents_commands = general_education_commands.CompleterEmplacementsDocumentsParCandidatCommand

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])
