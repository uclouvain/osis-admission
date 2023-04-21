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

from admission.ddd.admission.domain.service.i_emplacements_documents_demande import (
    IEmplacementsDocumentsDemandeTranslator,
)
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.enums.emplacement_document import TypeDocument, StatutDocument
from admission.exports.admission_recap.section import get_sections


class EmplacementsDocumentsDemandeInMemoryTranslator(IEmplacementsDocumentsDemandeTranslator):
    @classmethod
    def recuperer(
        cls,
        resume_dto: ResumePropositionDTO,
        questions_specifiques: List[QuestionSpecifiqueDTO],
    ) -> List[EmplacementDocumentDTO]:
        # Get the requested attachments by tab
        sections = get_sections(
            context=resume_dto,
            specific_questions=questions_specifiques,
            additional_documents=True,
        )

        requested_documents = resume_dto.proposition.documents_demandes

        documents = []

        # Add 'NON_LIBRE' documents
        for section in sections:
            for attachment in section.attachments:
                document_id = f'{section.identifier}.{attachment.identifier}'
                requested_document = requested_documents.get(document_id, {})
                document = EmplacementDocumentDTO(
                    uuid_demande=resume_dto.proposition.uuid,
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
                    justification_gestionnaire=requested_document.get('reason', ''),
                    soumis_le=requested_document.get('uploaded_at')
                    and parse_datetime(requested_document['uploaded_at']),
                    reclame_le=requested_document.get('requested_at')
                    and parse_datetime(requested_document['requested_at']),
                    a_echeance_le=requested_document.get('deadline_at')
                    and parse_datetime(requested_document['deadline_at']),
                    derniere_action_le=requested_document.get('last_action_at')
                    and parse_datetime(requested_document['last_action_at']),
                )
                documents.append(document)
        return documents
