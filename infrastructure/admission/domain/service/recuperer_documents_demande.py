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

from django.utils.dateparse import parse_datetime

from admission.ddd.admission.domain.service.i_recuperer_documents_demande import IRecupererDocumentsDemandeTranslator
from admission.ddd.admission.dtos.document import DocumentDTO
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.enums.document import TypeDocument, StatutDocument
from admission.exports.admission_recap.section import get_sections
from osis_document.api.utils import get_remote_tokens, get_several_remote_metadata


class RecupererDocumentsDemandeTranslator(IRecupererDocumentsDemandeTranslator):
    @classmethod
    def recuperer(
        cls,
        resume_dto: ResumePropositionDTO,
        questions_specifiques: List[QuestionSpecifiqueDTO],
    ) -> List[DocumentDTO]:
        # Get the requested attachments by tab
        sections = get_sections(resume_dto, questions_specifiques)

        # Get a read token and metadata of all attachments
        all_file_uuids = [
            str(file_uuid)
            for section in sections
            for attachment in section.attachments
            for file_uuid in attachment.uuids
        ]

        file_tokens = get_remote_tokens(all_file_uuids)
        file_metadata = get_several_remote_metadata(list(file_tokens.values()))

        requested_documents = resume_dto.proposition.documents_demandes
        documents = []

        # Add 'NON_LIBRE' documents
        for section in sections:
            for attachment in section.attachments:
                document_id = f'{section.identifier}.{attachment.identifier}'
                requested_document = requested_documents.get(document_id, {})
                metadata = (
                    file_metadata[file_tokens[attachment.uuids[0]]]
                    if attachment.uuids
                    and attachment.uuids[0] in file_tokens
                    and file_tokens[attachment.uuids[0]] in file_metadata
                    else {}
                )
                document = DocumentDTO(
                    identifiant=document_id,
                    onglet=section.identifier,
                    nom_onglet=section.label,
                    libelle=attachment.label,
                    uuids=attachment.uuids,
                    auteur=requested_document.get('author', resume_dto.proposition.login_candidat),
                    type=TypeDocument.NON_LIBRE.name,
                    statut=requested_document['status']
                    if 'status' in requested_document
                    else StatutDocument.A_RECLAMER.name
                    if (attachment.required and not attachment.uuids)
                    else StatutDocument.NON_ANALYSE.name,
                    requis=attachment.required,
                    justification_gestionnaire=requested_document.get('reason', ''),
                    soumis_le=metadata.get('uploaded_at') and parse_datetime(metadata['uploaded_at']),
                    reclame_le=requested_document.get('requested_at')
                    and parse_datetime(requested_document['requested_at']),
                    a_echeance_le=requested_document.get('deadline_at')
                    and parse_datetime(requested_document['deadline_at']),
                    derniere_action_le=requested_document.get('last_action_at')
                    and parse_datetime(requested_document['last_action_at']),
                )
                documents.append(document)
        return documents
