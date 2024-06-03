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
import abc
from typing import List, Dict

from django.utils.dateparse import parse_datetime, parse_date

from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    IdentifiantBaseEmplacementDocument,
    DocumentsSysteme,
)
from admission.exports.admission_recap.attachments import Attachment
from admission.exports.admission_recap.section import get_sections, Section
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import IPersonneConnueUclTranslator
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO
from osis_common.ddd import interface


class IEmplacementsDocumentsPropositionTranslator(interface.DomainService):
    @classmethod
    @abc.abstractmethod
    def recuperer_metadonnees_par_uuid_document(cls, uuids_documents: List[str]) -> dict:
        raise NotImplementedError

    @classmethod
    def recuperer_acteurs_dto_par_matricule(
        cls,
        personne_connue_translator: IPersonneConnueUclTranslator,
        metadonnees: dict,
        documents_reclames: dict,
    ) -> Dict[str, PersonneConnueUclDTO]:
        matricules_acteurs = set()
        for donnees in metadonnees.values():
            matricules_acteurs.add(donnees.get('author'))
        for document in documents_reclames.values():
            matricules_acteurs.add(document.get('last_actor'))
        return {
            person.matricule: person for person in personne_connue_translator.search_by_matricules(matricules_acteurs)
        }

    @classmethod
    def recuperer_emplacements_dto(
        cls,
        resume_dto: ResumePropositionDTO,
        questions_specifiques: List[QuestionSpecifiqueDTO],
        personne_connue_translator: IPersonneConnueUclTranslator,
        avec_documents_libres=True,
    ) -> List[EmplacementDocumentDTO]:
        # Get the requested documents by tab
        sections = get_sections(
            context=resume_dto,
            specific_questions=questions_specifiques,
            with_free_requestable_documents=avec_documents_libres,
        )

        # Get a read token and metadata of all documents
        uuids_documents = [
            uuid_document
            for section in sections
            for attachment in section.attachments
            for uuid_document in attachment.uuids
        ]

        # Add the 'LIBRE' documents uploaded by the managers
        if avec_documents_libres:
            for champ_documents_libres in [
                'documents_libres_sic_uclouvain',
                'documents_libres_fac_uclouvain',
            ]:
                for uuid_document in getattr(resume_dto.proposition, champ_documents_libres):
                    uuids_documents.append(str(uuid_document))

        # Add the documents generated by the system
        if resume_dto.est_proposition_generale:
            documents_systeme = (
                ('DOSSIER_ANALYSE', resume_dto.proposition.pdf_recapitulatif),
                ('ATTESTATION_ACCORD_FACULTAIRE', resume_dto.proposition.certificat_approbation_fac),
                ('ATTESTATION_REFUS_FACULTAIRE', resume_dto.proposition.certificat_refus_fac),
                ('ATTESTATION_ACCORD_SIC', resume_dto.proposition.certificat_approbation_sic),
                ('ATTESTATION_ACCORD_ANNEXE_SIC', resume_dto.proposition.certificat_approbation_sic_annexe),
                ('ATTESTATION_REFUS_SIC', resume_dto.proposition.certificat_refus_sic),
            )
        else:
            documents_systeme = (('DOSSIER_ANALYSE', resume_dto.proposition.pdf_recapitulatif),)

        for _, uuids_document_systeme in documents_systeme:
            for uuid_document_systeme in uuids_document_systeme:
                uuids_documents.append(str(uuid_document_systeme))

        metadonnees = cls.recuperer_metadonnees_par_uuid_document(uuids_documents)

        # Get all information about the actors
        acteurs = cls.recuperer_acteurs_dto_par_matricule(
            personne_connue_translator=personne_connue_translator,
            metadonnees=metadonnees,
            documents_reclames=resume_dto.proposition.documents_demandes,
        )

        # Add all documents that are or were requested to the candidate
        documents = [
            cls.get_emplacement_document_reclamables(
                uuid_proposition=resume_dto.proposition.uuid,
                document=document,
                section=section,
                metadonnees=metadonnees,
                documents_demandes=resume_dto.proposition.documents_demandes,
                acteurs=acteurs,
            )
            for section in sections
            for document in section.attachments
        ]

        if avec_documents_libres:
            # Add the 'LIBRE' documents uploaded by the managers
            for type_document, uuids_documents in [
                (TypeEmplacementDocument.LIBRE_INTERNE_FAC, resume_dto.proposition.documents_libres_fac_uclouvain),
                (TypeEmplacementDocument.LIBRE_INTERNE_SIC, resume_dto.proposition.documents_libres_sic_uclouvain),
            ]:
                for uuid_document in uuids_documents:
                    documents.append(
                        cls.get_emplacement_document_libre_non_reclamable(
                            uuid_proposition=resume_dto.proposition.uuid,
                            uuid_document=str(uuid_document),
                            type_document=type_document,
                            metadonnees=metadonnees,
                            acteurs=acteurs,
                        )
                    )

        # Add the documents generated by the system
        for identifiant_domaine, uuid_document in documents_systeme:
            if uuid_document:
                documents.append(
                    cls.get_emplacement_document_systeme(
                        uuid_proposition=resume_dto.proposition.uuid,
                        uuids_document=[str(uuid_doc) for uuid_doc in uuid_document],
                        identifiant_domaine=identifiant_domaine,
                        metadonnees=metadonnees,
                        acteurs=acteurs,
                    ),
                )

        return documents

    @classmethod
    def recuperer_emplacements_dto_proposition_continue(
        cls,
        resume_dto: ResumePropositionDTO,
        questions_specifiques: List[QuestionSpecifiqueDTO],
        personne_connue_translator: IPersonneConnueUclTranslator,
    ) -> List[EmplacementDocumentDTO]:
        # Get the requested documents by tab
        sections = get_sections(
            context=resume_dto,
            specific_questions=questions_specifiques,
        )

        # Get a read token and metadata of all documents
        uuids_documents = [
            uuid_document
            for section in sections
            for attachment in section.attachments
            for uuid_document in attachment.uuids
        ]

        # Add the documents generated by the system
        documents_systeme = (('DOSSIER_ANALYSE', resume_dto.proposition.pdf_recapitulatif),)

        for _, uuids_document_systeme in documents_systeme:
            for uuid_document_systeme in uuids_document_systeme:
                uuids_documents.append(str(uuid_document_systeme))

        metadonnees = cls.recuperer_metadonnees_par_uuid_document(uuids_documents)

        # Get all information about the actors
        acteurs = cls.recuperer_acteurs_dto_par_matricule(
            personne_connue_translator=personne_connue_translator,
            metadonnees=metadonnees,
            documents_reclames={},
        )

        # Add all documents that are or were requested to the candidate
        documents = [
            cls.get_emplacement_document_reclamables(
                uuid_proposition=resume_dto.proposition.uuid,
                document=document,
                section=section,
                metadonnees=metadonnees,
                documents_demandes={},
                acteurs=acteurs,
            )
            for section in sections
            for document in section.attachments
        ]

        # Add the documents generated by the system
        for identifiant_domaine, uuid_document in documents_systeme:
            if uuid_document:
                documents.append(
                    cls.get_emplacement_document_systeme(
                        uuid_proposition=resume_dto.proposition.uuid,
                        uuids_document=[str(uuid_doc) for uuid_doc in uuid_document],
                        identifiant_domaine=identifiant_domaine,
                        metadonnees=metadonnees,
                        acteurs=acteurs,
                    ),
                )

        return documents

    @classmethod
    def recuperer_emplacements_dto_proposition_doctorale(
        cls,
        resume_dto: ResumePropositionDTO,
        questions_specifiques: List[QuestionSpecifiqueDTO],
        personne_connue_translator: IPersonneConnueUclTranslator,
    ) -> List[EmplacementDocumentDTO]:
        # Get the requested documents by tab
        sections = get_sections(
            context=resume_dto,
            specific_questions=questions_specifiques,
        )

        # Get a read token and metadata of all documents
        uuids_documents = [
            uuid_document
            for section in sections
            for attachment in section.attachments
            for uuid_document in attachment.uuids
        ]

        # Add the documents generated by the system
        documents_systeme = (('DOSSIER_ANALYSE', resume_dto.proposition.pdf_recapitulatif),)

        for _, uuids_document_systeme in documents_systeme:
            for uuid_document_systeme in uuids_document_systeme:
                uuids_documents.append(str(uuid_document_systeme))

        metadonnees = cls.recuperer_metadonnees_par_uuid_document(uuids_documents)

        # Get all information about the actors
        acteurs = cls.recuperer_acteurs_dto_par_matricule(
            personne_connue_translator=personne_connue_translator,
            metadonnees=metadonnees,
            documents_reclames={},
        )

        # Add all documents that are or were requested to the candidate
        documents = [
            cls.get_emplacement_document_reclamables(
                uuid_proposition=resume_dto.proposition.uuid,
                document=document,
                section=section,
                metadonnees=metadonnees,
                documents_demandes={},
                acteurs=acteurs,
            )
            for section in sections
            for document in section.attachments
        ]

        # Add the documents generated by the system
        for identifiant_domaine, uuid_document in documents_systeme:
            if uuid_document:
                documents.append(
                    cls.get_emplacement_document_systeme(
                        uuid_proposition=resume_dto.proposition.uuid,
                        uuids_document=[str(uuid_doc) for uuid_doc in uuid_document],
                        identifiant_domaine=identifiant_domaine,
                        metadonnees=metadonnees,
                        acteurs=acteurs,
                    ),
                )

        return documents

    @classmethod
    def get_emplacement_document_reclamables(
        cls,
        uuid_proposition: str,
        document: Attachment,
        section: Section,
        metadonnees: dict,
        documents_demandes: dict,
        acteurs: Dict[str, PersonneConnueUclDTO],
    ) -> EmplacementDocumentDTO:
        document_id = f'{section.identifier}.{document.identifier}'
        document_demande = documents_demandes.get(document_id, {})
        metadonnees_document = metadonnees.get(document.uuids[0], {}) if document.uuids else {}
        types_documents = {}
        noms_documents_televerses = {}
        for uuid_document in document.uuids:
            metadonnees_courantes = metadonnees.get(uuid_document, {})
            types_documents[uuid_document] = metadonnees_courantes.get('mimetype') or ''
            noms_documents_televerses[uuid_document] = metadonnees_courantes.get('name') or ''
        est_requis_et_manquant = document.required and not document.uuids
        return EmplacementDocumentDTO(
            identifiant=document_id,
            libelle=document.label,
            libelle_langue_candidat=document.candidate_language_label,
            document_uuids=document.uuids,
            type=document_demande.get('type', TypeEmplacementDocument.NON_LIBRE.name),
            statut=document_demande['status']
            if 'status' in document_demande
            else StatutEmplacementDocument.A_RECLAMER.name
            if est_requis_et_manquant
            else StatutEmplacementDocument.NON_ANALYSE.name,
            justification_gestionnaire=document_demande.get('reason', ''),
            reclame_le=parse_datetime(document_demande['requested_at'])
            if document_demande.get('requested_at')
            else None,
            dernier_acteur=acteurs.get(document_demande['last_actor']) if document_demande.get('last_actor') else None,
            derniere_action_le=parse_datetime(document_demande['last_action_at'])
            if document_demande.get('last_action_at')
            else None,
            a_echeance_le=parse_date(document_demande['deadline_at']) if document_demande.get('deadline_at') else None,
            onglet=section.identifier,
            nom_onglet=section.label,
            nom_onglet_langue_candidat=section.candidate_language_label,
            uuid_proposition=uuid_proposition,
            document_soumis_par=acteurs.get(metadonnees_document['author'])
            if metadonnees_document.get('author')
            else None,
            document_soumis_le=parse_datetime(metadonnees_document['uploaded_at'])
            if metadonnees_document.get('uploaded_at')
            else None,
            requis_automatiquement=est_requis_et_manquant,
            types_documents=types_documents,
            noms_documents_televerses=noms_documents_televerses,
            statut_reclamation=document_demande.get('request_status', ''),
            onglet_checklist_associe=document_demande.get('related_checklist_tab') or '',
        )

    @classmethod
    def get_emplacement_document_libre_non_reclamable(
        cls,
        uuid_proposition: str,
        uuid_document: str,
        type_document: TypeEmplacementDocument,
        metadonnees: dict,
        acteurs: Dict[str, PersonneConnueUclDTO],
    ) -> EmplacementDocumentDTO:
        metadonnees_document = metadonnees.get(uuid_document, {})
        base_identifier = IdentifiantBaseEmplacementDocument.LIBRE_GESTIONNAIRE

        return EmplacementDocumentDTO(
            identifiant=f'{base_identifier.name}.{uuid_document}',
            libelle=metadonnees_document.get('explicit_name', ''),
            libelle_langue_candidat=metadonnees_document.get('explicit_name', ''),
            document_uuids=[uuid_document],
            type=type_document.name,
            statut=StatutEmplacementDocument.VALIDE.name,
            justification_gestionnaire='',
            document_soumis_par=acteurs.get(metadonnees_document['author'])
            if metadonnees_document.get('author')
            else None,
            document_soumis_le=parse_datetime(metadonnees_document['uploaded_at'])
            if metadonnees_document.get('uploaded_at')
            else None,
            reclame_le=None,
            derniere_action_le=None,
            dernier_acteur=None,
            a_echeance_le=None,
            onglet=base_identifier.name,
            nom_onglet=base_identifier.value,
            nom_onglet_langue_candidat=base_identifier.value,
            uuid_proposition=uuid_proposition,
            requis_automatiquement=False,
            types_documents={uuid_document: metadonnees_document.get('mimetype') or ''},
            noms_documents_televerses={uuid_document: metadonnees_document.get('name') or ''},
            statut_reclamation='',
        )

    @classmethod
    def get_emplacement_document_systeme(
        cls,
        uuid_proposition: str,
        uuids_document: List[str],
        identifiant_domaine: str,
        metadonnees: dict,
        acteurs: Dict[str, PersonneConnueUclDTO],
    ) -> EmplacementDocumentDTO:
        metadonnees_document = metadonnees.get(uuids_document[0], {}) if uuids_document else {}
        base_identifier = IdentifiantBaseEmplacementDocument.SYSTEME
        types_documents = {}
        noms_documents_televerses = {}
        for uuid_document in uuids_document:
            metadonnees_courantes = metadonnees.get(uuid_document, {})
            types_documents[uuid_document] = metadonnees_courantes.get('mimetype') or ''
            noms_documents_televerses[uuid_document] = metadonnees_courantes.get('name') or ''
        return EmplacementDocumentDTO(
            identifiant=f'{base_identifier.name}.{identifiant_domaine}',
            libelle=DocumentsSysteme[identifiant_domaine],
            libelle_langue_candidat=DocumentsSysteme[identifiant_domaine],
            document_uuids=uuids_document,
            type=TypeEmplacementDocument.SYSTEME.name,
            statut=StatutEmplacementDocument.VALIDE.name,
            justification_gestionnaire='',
            document_soumis_par=acteurs.get(metadonnees_document['author'])
            if metadonnees_document.get('author')
            else None,
            document_soumis_le=parse_datetime(metadonnees_document['uploaded_at'])
            if metadonnees_document.get('uploaded_at')
            else None,
            reclame_le=None,
            derniere_action_le=None,
            dernier_acteur=None,
            a_echeance_le=None,
            onglet=base_identifier.name,
            nom_onglet=base_identifier.value,
            nom_onglet_langue_candidat=base_identifier.value,
            uuid_proposition=uuid_proposition,
            requis_automatiquement=False,
            types_documents=types_documents,
            noms_documents_televerses=noms_documents_televerses,
            statut_reclamation='',
        )

    @classmethod
    def recuperer_emplacements_reclames_dto(
        cls,
        personne_connue_translator: IPersonneConnueUclTranslator,
        resume_dto: ResumePropositionDTO,
        questions_specifiques: List[QuestionSpecifiqueDTO],
    ) -> List[EmplacementDocumentDTO]:
        # Get the requested documents by tab
        sections = get_sections(
            context=resume_dto,
            specific_questions=questions_specifiques,
            with_free_requestable_documents=True,
        )

        # Get a read token and metadata of all documents
        # Add all documents that are or were requested to the candidate
        uuids_documents = [
            file_uuid for section in sections for attachment in section.attachments for file_uuid in attachment.uuids
        ]

        metadonnees = cls.recuperer_metadonnees_par_uuid_document(uuids_documents)

        # Get all information about the actors
        acteurs = cls.recuperer_acteurs_dto_par_matricule(
            personne_connue_translator=personne_connue_translator,
            metadonnees=metadonnees,
            documents_reclames=resume_dto.proposition.documents_demandes,
        )

        documents = []

        # Add all documents that are or were requested to the candidate
        for section in sections:
            for fichier in section.attachments:
                document = cls.get_emplacement_document_reclamables(
                    uuid_proposition=resume_dto.proposition.uuid,
                    document=fichier,
                    section=section,
                    metadonnees=metadonnees,
                    documents_demandes=resume_dto.proposition.documents_demandes,
                    acteurs=acteurs,
                )
                if document.statut == StatutEmplacementDocument.RECLAME.name:
                    documents.append(document)

        return documents

    @classmethod
    def recuperer_emplacements_documents_non_libres_dto(
        cls,
        personne_connue_translator: IPersonneConnueUclTranslator,
        resume_dto: ResumePropositionDTO,
        questions_specifiques: List[QuestionSpecifiqueDTO],
    ) -> List[EmplacementDocumentDTO]:
        # Get the requested documents by tab
        sections = get_sections(
            context=resume_dto,
            specific_questions=questions_specifiques,
            with_free_requestable_documents=False,
        )

        # Get a read token and metadata of all documents
        # Add all documents that are or were requested to the candidate
        uuids_documents = [
            file_uuid for section in sections for attachment in section.attachments for file_uuid in attachment.uuids
        ]

        metadonnees = cls.recuperer_metadonnees_par_uuid_document(uuids_documents)

        # Get all information about the actors
        acteurs = cls.recuperer_acteurs_dto_par_matricule(
            personne_connue_translator=personne_connue_translator,
            metadonnees=metadonnees,
            documents_reclames=resume_dto.proposition.documents_demandes,
        )

        documents = []

        # Add all documents that are or were requested to the candidate
        for section in sections:
            for fichier in section.attachments:
                documents.append(
                    cls.get_emplacement_document_reclamables(
                        uuid_proposition=resume_dto.proposition.uuid,
                        document=fichier,
                        section=section,
                        metadonnees=metadonnees,
                        documents_demandes=resume_dto.proposition.documents_demandes,
                        acteurs=acteurs,
                    )
                )

        return documents
