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

from admission.ddd.admission.domain.model.demande import DemandeIdentity
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument, EmplacementDocumentIdentity
from admission.ddd.admission.domain.service.i_emplacements_documents_demande import (
    IEmplacementsDocumentsDemandeTranslator,
)
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.enums.emplacement_document import TypeDocument, StatutDocument, OngletsDemande
from admission.exports.admission_recap.section import get_sections
from osis_document.api.utils import get_remote_tokens, get_several_remote_metadata


class EmplacementsDocumentsDemandeTranslator(IEmplacementsDocumentsDemandeTranslator):
    @classmethod
    def recuperer_emplacements_dto(
        cls,
        resume_dto: ResumePropositionDTO,
        questions_specifiques: List[QuestionSpecifiqueDTO],
    ) -> List[EmplacementDocumentDTO]:
        documents = cls.recuperer_emplacements(resume_dto, questions_specifiques)
        return [
            EmplacementDocumentDTO(
                identifiant=document.entity_id.identifiant,
                libelle=document.libelle,
                uuids=document.uuids,
                auteur=document.auteur,
                type=document.type.name,
                statut=document.statut.name,
                justification_gestionnaire=document.justification_gestionnaire,
                soumis_le=document.soumis_le,
                reclame_le=document.reclame_le,
                derniere_action_le=document.derniere_action_le,
                a_echeance_le=document.a_echeance_le,
                onglet=document.onglet.name,
                nom_onglet=document.onglet.value,
                uuid_demande=document.demande.uuid,
            )
            for document in documents
        ]

    @classmethod
    def recuperer_emplacements(
        cls,
        resume_dto: ResumePropositionDTO,
        questions_specifiques: List[QuestionSpecifiqueDTO],
    ) -> List[EmplacementDocument]:
        # Get the requested documents by tab
        tabs = get_sections(
            context=resume_dto,
            specific_questions=questions_specifiques,
            additional_documents=True,
        )

        # Get a read token and metadata of all documents
        all_file_uuids = [
            file_uuid for section in tabs for attachment in section.attachments for file_uuid in attachment.uuids
        ]

        for champ_documents_libres in [
            'documents_libres_sic_candidats',
            'documents_libres_fac_candidats',
            'documents_libres_fac_uclouvain',
            'documents_libres_fac_uclouvain',
        ]:
            for document_uuid in getattr(resume_dto.proposition, champ_documents_libres):
                all_file_uuids.append(str(document_uuid))

        file_tokens = get_remote_tokens(all_file_uuids)
        file_metadata = get_several_remote_metadata(list(file_tokens.values()))

        documents = []

        # Add all documents that are or were requested to the candidate
        for tab in tabs:
            for attachment in tab.attachments:
                document = cls.get_emplacement_document_candidat(
                    uuid_demande=resume_dto.proposition.uuid,
                    attachment=attachment,
                    tab=tab,
                    file_metadata=file_metadata,
                    file_tokens=file_tokens,
                    requested_documents=resume_dto.proposition.documents_demandes,
                )
                documents.append(document)

        # Add the 'LIBRE' documents uploaded by the managers
        for document_type, document_uuids in [
            (TypeDocument.CANDIDAT_FAC, resume_dto.proposition.documents_libres_fac_candidats),
            (TypeDocument.CANDIDAT_SIC, resume_dto.proposition.documents_libres_sic_candidats),
            (TypeDocument.INTERNE_FAC, resume_dto.proposition.documents_libres_sic_uclouvain),
            (TypeDocument.INTERNE_SIC, resume_dto.proposition.documents_libres_sic_uclouvain),
        ]:
            for document_uuid in document_uuids:
                documents.append(
                    cls.get_emplacement_document_gestionnaire(
                        uuid_proposition=resume_dto.proposition.uuid,
                        document_uuid=str(document_uuid),
                        document_type=document_type,
                        file_metadata=file_metadata,
                        file_tokens=file_tokens,
                    )
                )

        return documents

    @classmethod
    def get_emplacement_document_candidat(
        cls,
        uuid_demande,
        attachment,
        tab,
        file_metadata,
        file_tokens,
        requested_documents,
    ) -> EmplacementDocument:
        document_id = f'{tab.identifier}.{attachment.identifier}'
        requested_document = requested_documents.get(document_id, {})
        metadata = (
            file_metadata[file_tokens[attachment.uuids[0]]]
            if attachment.uuids
            and attachment.uuids[0] in file_tokens
            and file_tokens[attachment.uuids[0]] in file_metadata
            else {}
        )
        return EmplacementDocument(
            demande=DemandeIdentity(uuid=uuid_demande),
            entity_id=EmplacementDocumentIdentity(identifiant=document_id),
            onglet=tab.base_identifier,
            libelle=attachment.label,
            uuids=attachment.uuids,
            auteur=requested_document.get('author', ''),
            type=TypeDocument[requested_document['type']] if 'type' in requested_document else TypeDocument.NON_LIBRE,
            statut=StatutDocument[requested_document['status']]
            if 'status' in requested_document
            else StatutDocument.A_RECLAMER
            if (attachment.required and not attachment.uuids)
            else StatutDocument.NON_ANALYSE,
            justification_gestionnaire=requested_document.get('reason', ''),
            soumis_le=metadata.get('uploaded_at') and parse_datetime(metadata['uploaded_at']),
            reclame_le=requested_document.get('requested_at') and parse_datetime(requested_document['requested_at']),
            a_echeance_le=requested_document.get('deadline_at') and parse_datetime(requested_document['deadline_at']),
            derniere_action_le=requested_document.get('last_action_at')
            and parse_datetime(requested_document['last_action_at']),
        )

    @classmethod
    def get_emplacement_document_gestionnaire(
        cls,
        uuid_proposition,
        document_uuid,
        document_type,
        file_metadata,
        file_tokens,
    ) -> EmplacementDocument:
        metadata = (
            file_metadata[file_tokens[document_uuid]]
            if document_uuid in file_tokens and file_tokens[document_uuid] in file_metadata
            else {}
        )

        return EmplacementDocument(
            demande=DemandeIdentity(uuid=uuid_proposition),
            entity_id=EmplacementDocumentIdentity(f'{OngletsDemande.DOCUMENTS_ADDITIONNELS.name}.{document_uuid}'),
            onglet=OngletsDemande.DOCUMENTS_ADDITIONNELS,
            libelle=metadata.get('explicit_name', ''),
            uuids=[document_uuid],
            auteur=metadata.get('author', ''),
            type=document_type,
            statut=StatutDocument.VALIDE,
            justification_gestionnaire='',
            soumis_le=metadata.get('uploaded_at') and parse_datetime(metadata['uploaded_at']),
            reclame_le=None,
            a_echeance_le=None,
            derniere_action_le=None,
        )
