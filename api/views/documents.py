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
import os
import uuid
from typing import List

from django.utils.text import slugify
from osis_document.enums import PostProcessingType
from rest_framework import generics
from rest_framework.response import Response

from admission.api import serializers
from admission.api.schema import ResponseSpecificSchema
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.emplacement_document import (
    DOCUMENTS_A_NE_PAS_CONVERTIR_A_LA_SOUMISSION,
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.formation_generale import commands as general_education_commands
from admission.ddd.admission.formation_continue import commands as continuing_education_commands
from admission.ddd.admission.doctorat.preparation import commands as doctorate_education_commands
from admission.exceptions import DocumentPostProcessingException
from admission.utils import (
    get_cached_general_education_admission_perm_obj,
    get_cached_continuing_education_admission_perm_obj,
    get_cached_admission_perm_obj,
)
from base.forms.utils.file_field import PDF_MIME_TYPE
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class RequestedDocumentsListSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.DocumentSpecificQuestionsListSerializer,
        'POST': (
            serializers.CompleterEmplacementsDocumentsParCandidatCommandSerializer,
            serializers.PropositionIdentityDTOSerializer,
        ),
    }
    # Force schema to return an object (so that we have the two lists and the date)
    list_force_object = True


class RequestedDocumentListView(APIPermissionRequiredMixin, generics.ListCreateAPIView):
    name = "documents"
    schema = RequestedDocumentsListSchema()
    serializer_class = serializers.DocumentSpecificQuestionsListSerializer
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

        immediate_requested_documents = []
        later_requested_documents = []

        for document in requested_documents:
            if document.statut_reclamation == StatutReclamationEmplacementDocument.IMMEDIATEMENT.name:
                immediate_requested_documents.append(document)
            else:
                later_requested_documents.append(document)

        serializer = self.get_serializer(
            {
                'immediate_requested_documents': immediate_requested_documents,
                'later_requested_documents': later_requested_documents,
                'deadline': immediate_requested_documents[0].a_echeance_le if immediate_requested_documents else None,
            }
        )

        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        from osis_document.api.utils import get_several_remote_metadata, launch_post_processing

        input_serializer = serializers.CompleterEmplacementsDocumentsParCandidatCommandSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        requested_documents: List[EmplacementDocumentDTO] = message_bus_instance.invoke(
            self.get_documents_command(
                uuid_proposition=self.kwargs['uuid'],
            )
        )

        requested_documents_by_identifier = {document.identifiant: document for document in requested_documents}

        # If necessary, merge each document field into one PDF
        final_documents = {}

        metadata = get_several_remote_metadata(
            [
                document_uuid
                for document_uuids in input_serializer.validated_data['reponses_documents_a_completer'].values()
                for document_uuid in document_uuids
            ]
        )

        for identifier, document_tokens in input_serializer.validated_data['reponses_documents_a_completer'].items():
            post_processing_types = []
            post_processing_params = {
                PostProcessingType.MERGE.name: {},
                PostProcessingType.CONVERT.name: {},
            }

            if any(metadata[document_token]['mimetype'] != PDF_MIME_TYPE for document_token in document_tokens):
                # If the file is not a PDF, convert it
                post_processing_types.append(PostProcessingType.CONVERT.name)

            if len(document_tokens) > 1:
                # If there is more than one file, merge them
                post_processing_types.append(PostProcessingType.MERGE.name)
                filename = slugify(requested_documents_by_identifier[identifier].libelle_langue_candidat)
                post_processing_params[PostProcessingType.MERGE.name]['output_filename'] = f'{filename}.pdf'
            elif post_processing_types:
                # If there is only one file which is not a PDF, convert it
                filename, _ = os.path.splitext(metadata[document_tokens[0]]['name'])
                post_processing_params[PostProcessingType.CONVERT.name]['output_filename'] = f'{filename}.pdf'

            if not post_processing_types or identifier in DOCUMENTS_A_NE_PAS_CONVERTIR_A_LA_SOUMISSION:
                final_documents[identifier] = document_tokens
                continue

            result = launch_post_processing(
                uuid_list=[metadata[document_token]['upload_uuid'] for document_token in document_tokens],
                post_processing_types=post_processing_types,
                post_process_params=post_processing_params,
                async_post_processing=False,
            )

            if result.get('error'):
                raise DocumentPostProcessingException(result['error'])

            final_documents[identifier] = [
                uuid.UUID(
                    result[
                        PostProcessingType.MERGE.name
                        if result[PostProcessingType.MERGE.name].get('output')
                        else PostProcessingType.CONVERT.name
                    ]['output']['upload_objects'][0]
                )
            ]

        command_result = message_bus_instance.invoke(
            self.complete_documents_commands(
                uuid_proposition=self.kwargs['uuid'],
                reponses_documents_a_completer=final_documents,
            )
        )

        output_serializer = serializers.PropositionIdentityDTOSerializer(instance=command_result)

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


class ContinuingRequestedDocumentListView(RequestedDocumentListView):
    name = "continuing_documents"
    permission_mapping = {
        'GET': 'admission.view_continuingeducationadmission_documents',
        'POST': 'admission.change_continuingeducationadmission_documents',
    }
    schema = RequestedDocumentsListSchema(operation_id_base='_continuing_documents')

    get_documents_command = continuing_education_commands.RecupererDocumentsReclamesPropositionQuery
    complete_documents_commands = continuing_education_commands.CompleterEmplacementsDocumentsParCandidatCommand

    def get_permission_object(self):
        return get_cached_continuing_education_admission_perm_obj(self.kwargs['uuid'])


class DoctorateRequestedDocumentListView(RequestedDocumentListView):
    name = "doctorate_documents"
    permission_mapping = {
        'GET': 'admission.view_admission_documents',
        'POST': 'admission.change_admission_documents',
    }
    schema = RequestedDocumentsListSchema(operation_id_base='_doctorate_documents')

    get_documents_command = doctorate_education_commands.RecupererDocumentsReclamesPropositionQuery
    complete_documents_commands = doctorate_education_commands.CompleterEmplacementsDocumentsParCandidatCommand

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])
