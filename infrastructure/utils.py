# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

import uuid
from email.message import EmailMessage
from typing import Optional, List, Dict
from uuid import UUID

import attr
from django.conf import settings
from django.db.models import Model, Q, Func
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from admission.constants import SUPPORTED_MIME_TYPES
from admission.models import (
    SupervisionActor,
    AdmissionFormItem,
)
from admission.models.base import BaseAdmission
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums import CleConfigurationItemFormulaire
from admission.ddd.admission.enums.emplacement_document import (
    OngletsDemande,
    TypeEmplacementDocument,
    IdentifiantBaseEmplacementDocument,
    StatutEmplacementDocument,
)
from base.models.entity_version import EntityVersion, PEDAGOGICAL_ENTITY_ADDED_EXCEPTIONS
from base.models.enums.entity_type import PEDAGOGICAL_ENTITY_TYPES
from osis_profile.models import EducationalExperienceYear

FORMATTED_EMAIL_FOR_HISTORY = """{sender_label} : {sender}
{recipient_label} : {recipient}
{cc}{subject_label} : {subject}

{message}"""


def get_message_to_historize(message: EmailMessage) -> dict:
    """
    Get the message to be saved in the history.
    """
    plain_text_content = ""
    for part in message.walk():
        # Mail payload is decoded to bytes then decode to utf8
        if part.get_content_type() == "text/plain":
            plain_text_content = part.get_payload(decode=True).decode(settings.DEFAULT_CHARSET)

    format_args = {
        'sender_label': _("Sender"),
        'recipient_label': _("Recipient"),
        'subject_label': _("Subject"),
        'sender': message.get("From"),
        'recipient': message.get("To"),
        'cc': "CC : {}\n".format(message.get("Cc")) if message.get("Cc") else '',
        'subject': message.get("Subject"),
        'message': plain_text_content,
    }

    with translation.override(settings.LANGUAGE_CODE_FR):
        message_fr = FORMATTED_EMAIL_FOR_HISTORY.format(**format_args)
    with translation.override(settings.LANGUAGE_CODE_EN):
        message_en = FORMATTED_EMAIL_FOR_HISTORY.format(**format_args)

    return {
        settings.LANGUAGE_CODE_FR: message_fr,
        settings.LANGUAGE_CODE_EN: message_en,
    }


def get_requested_documents_html_lists(
    requested_documents: List[EmplacementDocument],
    requested_documents_dtos: List[EmplacementDocumentDTO],
):
    """
    Create an html list with the requested and submitted documents and an html list with the requested and not
    submitted documents.
    :param requested_documents: List of requested documents with the updated status
    :param requested_documents_dtos: List of requested documents dtos
    :return: a dict whose the keys are the documents statuses and the values, the html lists of documents grouped
    by tab.
    """
    updated_documents_by_identifier: Dict[str, EmplacementDocument] = {
        document.entity_id.identifiant: document for document in requested_documents
    }

    current_tab_by_status = {
        StatutEmplacementDocument.A_RECLAMER: None,
        StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION: None,
    }
    html_list_by_status = {
        StatutEmplacementDocument.A_RECLAMER: '',
        StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION: '',
    }

    for document_dto in requested_documents_dtos:
        updated_document = updated_documents_by_identifier.get(document_dto.identifiant)

        if updated_document and updated_document.statut in html_list_by_status:
            # Group the documents by tab
            if current_tab_by_status[updated_document.statut] != document_dto.onglet:
                if current_tab_by_status[updated_document.statut] is not None:
                    html_list_by_status[updated_document.statut] += '</ul></li>'

                # Add the tab name
                html_list_by_status[updated_document.statut] += f'<li>{document_dto.nom_onglet_langue_candidat}<ul>'

            # Add the document name
            html_list_by_status[updated_document.statut] += f'<li>{document_dto.libelle_langue_candidat}</li>'

            current_tab_by_status[updated_document.statut] = document_dto.onglet

    for status in html_list_by_status:
        if html_list_by_status[status]:
            html_list_by_status[status] = f'<ul>{html_list_by_status[status]}</ul></li></ul>'

    return html_list_by_status


def dto_to_dict(dto):
    """Make a shallow dict copy of a DTO."""
    return dict((field.name, getattr(dto, field.name)) for field in attr.fields(type(dto)))


FREE_MANAGER_DOCUMENT_TYPE_BY_MODEL_FIELD = {
    'uclouvain_sic_documents': TypeEmplacementDocument.LIBRE_INTERNE_SIC.name,
    'uclouvain_fac_documents': TypeEmplacementDocument.LIBRE_INTERNE_FAC.name,
}

MODEL_FIELD_BY_FREE_MANAGER_DOCUMENT_TYPE = {
    value: key for key, value in FREE_MANAGER_DOCUMENT_TYPE_BY_MODEL_FIELD.items()
}


@attr.dataclass(frozen=True)
class AdmissionDocument:
    obj: Model
    field: str
    uuids: List[UUID]
    type: str
    requestable: bool
    specific_question_uuid: str
    status: str
    reason: str
    requested_at: str
    deadline_at: str
    last_action_at: str
    last_actor: str
    automatically_required: Optional[bool]
    mimetypes: List[str]
    label: str
    label_fr: str
    label_en: str
    document_submitted_by: str
    max_documents_number: Optional[int]
    request_status: str
    related_checklist_tab: str


def get_document_from_identifier(
    admission: BaseAdmission,
    document_identifier: str,
) -> Optional[AdmissionDocument]:
    """
    Get information about a document placement based on its identifier and the related admission.
    The identifier is composed of:
    - [TAB_IDENTIFIER].QUESTION_SPECIFIQUE.[SPECIFIC_QUESTION_UUID] for a specific question
    - [TAB_IDENTIFIER].[DOMAIN_IDENTIFIER] for categorized documents. If a document belongs to a model different from
    the admission then the related object uuid is included between the base_identifier and the document identifiers.
    - LIBRE_GESTIONNAIRE.[DOCUMENT_UUID] for free documents uploaded by a manager
    - LIBRE_CANDIDAT.[SPECIFIC_QUESTION_UUID] for a requested free document
    - SYSTEME.[DOMAIN_IDENTIFIER] for internal documents that are generated by the system
    """
    field: str = ''
    obj: Optional[Model] = None
    document_type: str = ''
    document_uuids: List[UUID] = []
    requestable_document: bool = False
    specific_question_uuid: str = ''
    document_identifier_parts = document_identifier.split('.')
    identifiers_nb = len(document_identifier_parts)
    document_mimetypes: List[str] = []
    requested_document = admission.requested_documents.get(document_identifier, {})
    document_author: str = requested_document.get('last_actor', '')
    document_label: str = ''
    document_label_fr: str = ''
    document_label_en: str = ''
    document_submitted_by: str = ''
    metadata: dict = {}
    max_documents_number = None

    if identifiers_nb < 2:
        return

    base_identifier = document_identifier_parts[0]

    if (
        base_identifier == IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name
        or document_identifier_parts[1] == IdentifiantBaseEmplacementDocument.QUESTION_SPECIFIQUE.name
    ):
        # Documents based on specific questions

        if base_identifier == IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name:
            # Requested free documents
            # LIBRE_CANDIDAT.[SPECIFIC_QUESTION_UUID]
            if identifiers_nb != 2:
                return

            document_type = requested_document.get('type', '')

        else:
            # Non free document specified with a specific question
            # [TAB_IDENTIFIER].QUESTION_SPECIFIQUE.[SPECIFIC_QUESTION_UUID]
            if identifiers_nb != 3:
                return

            document_type = TypeEmplacementDocument.NON_LIBRE.name

        obj = admission
        field = 'specific_question_answers'
        specific_question_uuid = document_identifier_parts[-1]
        document_uuids = [
            uuid.UUID(document_uuid) if isinstance(document_uuid, str) else document_uuid
            for document_uuid in admission.specific_question_answers.get(specific_question_uuid, [])
        ]
        requestable_document = True
        document_status = requested_document.get('status', StatutEmplacementDocument.NON_ANALYSE.name)

        specific_question: AdmissionFormItem = AdmissionFormItem.objects.filter(
            uuid=specific_question_uuid,
        ).first()

        if not specific_question:
            return

        document_mimetypes = specific_question.configuration.get(
            CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name,
            [],
        )
        document_label = specific_question.title.get(admission.candidate.language, '')
        document_label_fr = specific_question.title.get(settings.LANGUAGE_CODE_FR, '')
        document_label_en = specific_question.title.get(settings.LANGUAGE_CODE_EN, '')
        max_documents_number = specific_question.configuration.get(
            CleConfigurationItemFormulaire.NOMBRE_MAX_DOCUMENTS.name,
        )

    elif base_identifier == IdentifiantBaseEmplacementDocument.LIBRE_GESTIONNAIRE.name:
        # Free documents uploaded by the manager
        # LIBRE_GESTIONNAIRE.[DOCUMENT_UUID]
        obj = admission
        document_status = StatutEmplacementDocument.VALIDE.name

        document_uuid = uuid.UUID(document_identifier_parts[1])
        field = next(
            (
                field
                for field in FREE_MANAGER_DOCUMENT_TYPE_BY_MODEL_FIELD.keys()
                if document_uuid in getattr(admission, field)
            ),
            '',
        )

        if not field:
            return

        document_uuids = [document_uuid]
        document_type = FREE_MANAGER_DOCUMENT_TYPE_BY_MODEL_FIELD[field]
        max_documents_number = 1

        if document_uuids:
            from osis_document.api.utils import get_remote_token, get_remote_metadata

            token = get_remote_token(uuid=document_uuids[0], for_modified_upload=True)
            metadata = get_remote_metadata(token=token) or {}
            document_author = metadata.get('author', '')
            document_label = metadata.get('explicit_name', '')
            document_label_fr = document_label
            document_label_en = document_label
            document_mimetypes = [metadata.get('mimetype')] or []

    elif base_identifier == IdentifiantBaseEmplacementDocument.SYSTEME.name:
        # System documents
        # SYSTEME.[DOMAIN_IDENTIFIER]
        if identifiers_nb != 2:
            return

        document_type = TypeEmplacementDocument.SYSTEME.name
        document_status = StatutEmplacementDocument.VALIDE.name
        domain_identifier = document_identifier_parts[1]

        obj = admission
        field = CORRESPONDANCE_CHAMPS_SYSTEME.get(domain_identifier, '')

        if obj and field:
            document_uuids = getattr(obj, field, [])
            model_attribute = type(obj)._meta.get_field(field)
            document_mimetypes = model_attribute.mimetypes
            max_documents_number = model_attribute.max_files

    # Categorized documents
    else:
        document_type = TypeEmplacementDocument.NON_LIBRE.name
        requestable_document = True
        domain_identifier = document_identifier_parts[-1]
        document_status = requested_document.get('status', StatutEmplacementDocument.NON_ANALYSE.name)

        if base_identifier == OngletsDemande.IDENTIFICATION.name:
            # IDENTIFICATION.[DOMAIN_IDENTIFIER]
            obj = admission.candidate
            field = CORRESPONDANCE_CHAMPS_IDENTIFICATION.get(domain_identifier)

        elif base_identifier == OngletsDemande.ETUDES_SECONDAIRES.name:
            # ETUDES_SECONDAIRES.[DOMAIN_IDENTIFIER]
            if domain_identifier in CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_BELGES:
                obj = getattr(admission.candidate, 'belgianhighschooldiploma', None)
                field = CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_BELGES[domain_identifier]
            elif domain_identifier in CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_ETRANGERES:
                obj = getattr(admission.candidate, 'foreignhighschooldiploma', None)
                field = CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_ETRANGERES[domain_identifier]
            elif domain_identifier in CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_ALTERNATIVES:
                obj = getattr(admission.candidate, 'highschooldiplomaalternative', None)
                field = CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_ALTERNATIVES[domain_identifier]

        elif base_identifier == OngletsDemande.LANGUES.name:
            # LANGUES.[CODE_LANGUE].[DOMAIN_IDENTIFIER]
            if not identifiers_nb == 3:
                return
            language_code = document_identifier_parts[1]
            obj = admission.candidate.languages_knowledge.filter(language__code=language_code).first()
            field = CORRESPONDANCE_CHAMPS_CONNAISSANCES_LANGUES.get(domain_identifier)

        elif base_identifier == OngletsDemande.CURRICULUM.name:
            if domain_identifier in CORRESPONDANCE_CHAMPS_CURRICULUM_BASE:
                # CURRICULUM.[DOMAIN_IDENTIFIER]
                obj = admission
                field = CORRESPONDANCE_CHAMPS_CURRICULUM_BASE[domain_identifier]

            elif domain_identifier in CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_ACADEMIQUE:
                # CURRICULUM.[EXPERIENCE_UUID].[DOMAIN_IDENTIFIER]
                if not identifiers_nb == 3:
                    return
                experience_uuid = document_identifier_parts[1]
                field = CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_ACADEMIQUE[domain_identifier]
                obj = admission.candidate.educationalexperience_set.filter(uuid=experience_uuid).first()

            elif domain_identifier in CORRESPONDANCE_CHAMPS_CURRICULUM_ANNEE_EXPERIENCE_ACADEMIQUE:
                # CURRICULUM.[EXPERIENCE_UUID].[EXPERIENCE_YEAR].[DOMAIN_IDENTIFIER]
                if not identifiers_nb == 4:
                    return
                experience_uuid = document_identifier_parts[1]
                experience_year = document_identifier_parts[2]
                field = CORRESPONDANCE_CHAMPS_CURRICULUM_ANNEE_EXPERIENCE_ACADEMIQUE[domain_identifier]
                obj = EducationalExperienceYear.objects.filter(
                    educational_experience__uuid=experience_uuid,
                    academic_year__year=experience_year,
                ).first()

            elif domain_identifier in CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_NON_ACADEMIQUE:
                # CURRICULUM.[EXPERIENCE_UUID].[DOMAIN_IDENTIFIER]
                if not identifiers_nb == 3:
                    return
                experience_uuid = document_identifier_parts[1]
                field = CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_NON_ACADEMIQUE[domain_identifier]
                obj = admission.candidate.professionalexperience_set.filter(uuid=experience_uuid).first()

        elif base_identifier == OngletsDemande.INFORMATIONS_ADDITIONNELLES.name:
            # INFORMATIONS_ADDITIONNELLES.[DOMAIN_IDENTIFIER]
            obj = admission
            field = CORRESPONDANCE_CHAMPS_INFORMATIONS_ADDITIONNELLES.get(domain_identifier)

        elif base_identifier == OngletsDemande.COMPTABILITE.name:
            # COMPTABILITE.[DOMAIN_IDENTIFIER]
            obj = admission.accounting
            field = CORRESPONDANCE_CHAMPS_COMPTABILITE.get(domain_identifier)

        elif base_identifier == OngletsDemande.PROJET.name:
            # PROJET.[DOMAIN_IDENTIFIER]
            obj = admission
            field = CORRESPONDANCE_CHAMPS_PROJET.get(domain_identifier)

        elif base_identifier == OngletsDemande.COTUTELLE.name:
            # COTUTELLE.[DOMAIN_IDENTIFIER]
            obj = admission
            field = CORRESPONDANCE_CHAMPS_COTUTELLE.get(domain_identifier)

        elif base_identifier == OngletsDemande.SUPERVISION.name:
            # SUPERVISION.[ACTOR_UUID].[DOMAIN_IDENTIFIER]
            if not identifiers_nb == 3:
                return
            actor_uuid = document_identifier_parts[1]
            obj = SupervisionActor.objects.filter(uuid=actor_uuid).first()
            field = CORRESPONDANCE_CHAMPS_SUPERVISION.get(domain_identifier)

        elif base_identifier == OngletsDemande.SUITE_AUTORISATION.name:
            # SUITE_AUTORISATION.[DOMAIN_IDENTIFIER]
            obj = admission
            field = CORRESPONDANCE_CHAMPS_AUTORISATION.get(domain_identifier)

        if obj and field:
            document_uuids = getattr(obj, field, [])
            model_attribute = type(obj)._meta.get_field(field)
            document_mimetypes = model_attribute.mimetypes
            max_documents_number = model_attribute.max_files

    if obj and field and document_type:
        if document_uuids:
            if not metadata:
                from osis_document.api.utils import get_remote_token, get_remote_metadata

                token = get_remote_token(uuid=document_uuids[0], for_modified_upload=True)
                metadata = get_remote_metadata(token=token)
            if metadata:
                document_submitted_by = metadata.get('author', '')

        return AdmissionDocument(
            obj=obj,
            field=field,
            uuids=document_uuids,
            type=document_type,
            requestable=requestable_document,
            specific_question_uuid=specific_question_uuid,
            status=document_status,
            reason=requested_document.get('reason') or '',
            requested_at=requested_document.get('requested_at') or '',
            deadline_at=requested_document.get('deadline_at') or '',
            last_action_at=requested_document.get('last_action_at') or '',
            last_actor=document_author,
            automatically_required=requested_document.get('automatically_required') or False,
            mimetypes=document_mimetypes or list(SUPPORTED_MIME_TYPES),
            label=document_label,
            label_fr=document_label_fr,
            label_en=document_label_en,
            document_submitted_by=document_submitted_by,
            max_documents_number=max_documents_number,
            request_status=requested_document.get('request_status') or '',
            related_checklist_tab=requested_document.get('related_checklist_tab') or '',
        )


CORRESPONDANCE_CHAMPS_IDENTIFICATION = {
    'PASSEPORT': 'passport',
    'CARTE_IDENTITE': 'id_card',
    'PHOTO_IDENTITE': 'id_photo',
}

CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_BELGES = {
    'DIPLOME_BELGE_DIPLOME': 'high_school_diploma',
}

CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_ETRANGERES = {
    'DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_UE': 'final_equivalence_decision_ue',
    'DIPLOME_ETRANGER_PREUVE_DECISION_EQUIVALENCE': 'equivalence_decision_proof',
    'DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_HORS_UE': 'final_equivalence_decision_not_ue',
    'DIPLOME_ETRANGER_DIPLOME': 'high_school_diploma',
    'DIPLOME_ETRANGER_TRADUCTION_DIPLOME': 'high_school_diploma_translation',
    'DIPLOME_ETRANGER_RELEVE_NOTES': 'high_school_transcript',
    'DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES': 'high_school_transcript_translation',
}

CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_ALTERNATIVES = {
    'ALTERNATIVE_SECONDAIRES_EXAMEN_ADMISSION_PREMIER_CYCLE': 'first_cycle_admission_exam',
}

CORRESPONDANCE_CHAMPS_CONNAISSANCES_LANGUES = {
    'CERTIFICAT_CONNAISSANCE_LANGUE': 'certificate',
}

CORRESPONDANCE_CHAMPS_CURRICULUM_BASE = {
    'DIPLOME_EQUIVALENCE': 'diploma_equivalence',
    'CURRICULUM': 'curriculum',
}

CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_ACADEMIQUE = {
    'RELEVE_NOTES': 'transcript',
    'TRADUCTION_RELEVE_NOTES': 'transcript_translation',
    'RESUME_MEMOIRE': 'dissertation_summary',
    'DIPLOME': 'graduate_degree',
    'TRADUCTION_DIPLOME': 'graduate_degree_translation',
}

CORRESPONDANCE_CHAMPS_CURRICULUM_ANNEE_EXPERIENCE_ACADEMIQUE = {
    'RELEVE_NOTES_ANNUEL': 'transcript',
    'TRADUCTION_RELEVE_NOTES_ANNUEL': 'transcript_translation',
}

CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_NON_ACADEMIQUE = {
    'CERTIFICAT_EXPERIENCE': 'certificate',
}

CHAMPS_DOCUMENTS_EXPERIENCES_CURRICULUM = (
    CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_ACADEMIQUE.keys()
    | CORRESPONDANCE_CHAMPS_CURRICULUM_ANNEE_EXPERIENCE_ACADEMIQUE.keys()
    | CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_NON_ACADEMIQUE.keys()
)

CORRESPONDANCE_CHAMPS_INFORMATIONS_ADDITIONNELLES = {
    'COPIE_TITRE_SEJOUR': 'residence_permit',
    'ATTESTATION_INSCRIPTION_REGULIERE': 'regular_registration_proof',
    'FORMULAIRE_MODIFICATION_INSCRIPTION': 'registration_change_form',
    'ADDITIONAL_DOCUMENTS': 'additional_documents',
}

CORRESPONDANCE_CHAMPS_COMPTABILITE = {
    'ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT': 'institute_absence_debts_certificate',
    'ATTESTATION_ENFANT_PERSONNEL': 'staff_child_certificate',
    'CARTE_RESIDENT_LONGUE_DUREE': 'long_term_resident_card',
    'CARTE_CIRE_SEJOUR_ILLIMITE_ETRANGER': 'cire_unlimited_stay_foreigner_card',
    'CARTE_SEJOUR_MEMBRE_UE': 'ue_family_member_residence_card',
    'CARTE_SEJOUR_PERMANENT_MEMBRE_UE': 'ue_family_member_permanent_residence_card',
    'CARTE_A_B_REFUGIE': 'refugee_a_b_card',
    'ANNEXE_25_26_REFUGIES_APATRIDES': 'refugees_stateless_annex_25_26',
    'ATTESTATION_IMMATRICULATION': 'registration_certificate',
    'CARTE_A_B': 'a_b_card',
    'DECISION_PROTECTION_SUBSIDIAIRE': 'subsidiary_protection_decision',
    'DECISION_PROTECTION_TEMPORAIRE': 'temporary_protection_decision',
    'TITRE_SEJOUR_3_MOIS_PROFESSIONEL': 'professional_3_month_residence_permit',
    'FICHES_REMUNERATION': 'salary_slips',
    'TITRE_SEJOUR_3_MOIS_REMPLACEMENT': 'replacement_3_month_residence_permit',
    'PREUVE_ALLOCATIONS_CHOMAGE_PENSION_INDEMNITE': 'unemployment_benefit_pension_compensation_proof',
    'ATTESTATION_CPAS': 'cpas_certificate',
    'COMPOSITION_MENAGE_ACTE_NAISSANCE': 'household_composition_or_birth_certificate',
    'ACTE_TUTELLE': 'tutorship_act',
    'COMPOSITION_MENAGE_ACTE_MARIAGE': 'household_composition_or_marriage_certificate',
    'ATTESTATION_COHABITATION_LEGALE': 'legal_cohabitation_certificate',
    'CARTE_IDENTITE_PARENT': 'parent_identity_card',
    'TITRE_SEJOUR_LONGUE_DUREE_PARENT': 'parent_long_term_residence_permit',
    'ANNEXE_25_26_REFUGIES_APATRIDES_DECISION_PROTECTION_PARENT': (
        'parent_refugees_stateless_annex_25_26_or_protection_decision'
    ),
    'TITRE_SEJOUR_3_MOIS_PARENT': 'parent_3_month_residence_permit',
    'FICHES_REMUNERATION_PARENT': 'parent_salary_slips',
    'ATTESTATION_CPAS_PARENT': 'parent_cpas_certificate',
    'DECISION_BOURSE_CFWB': 'cfwb_scholarship_decision',
    'ATTESTATION_BOURSIER': 'scholarship_certificate',
    'TITRE_IDENTITE_SEJOUR_LONGUE_DUREE_UE': 'ue_long_term_stay_identity_document',
    'TITRE_SEJOUR_BELGIQUE': 'belgium_residence_permit',
}

CORRESPONDANCE_CHAMPS_PROJET = {
    'PREUVE_BOURSE': 'scholarship_proof',
    'DOCUMENTS_PROJET': 'project_document',
    'PROPOSITION_PROGRAMME_DOCTORAL': 'program_proposition',
    'PROJET_FORMATION_COMPLEMENTAIRE': 'additional_training_project',
    'GRAPHE_GANTT': 'gantt_graph',
    'LETTRES_RECOMMANDATION': 'recommendation_letters',
}

CORRESPONDANCE_CHAMPS_COTUTELLE = {
    'DEMANDE_OUVERTURE': 'cotutelle_opening_request',
    'CONVENTION': 'cotutelle_convention',
    'AUTRES_DOCUMENTS': 'cotutelle_other_documents',
}

CORRESPONDANCE_CHAMPS_SUPERVISION = {
    'APPROBATION_PDF': 'pdf_from_candidate',
}

CORRESPONDANCE_CHAMPS_AUTORISATION = {
    'VISA_ETUDES': 'student_visa_d',
    'AUTORISATION_PDF_SIGNEE': 'signed_enrollment_authorization',
}

CORRESPONDANCE_CHAMPS_SYSTEME = {
    'DOSSIER_ANALYSE': 'pdf_recap',
    'ATTESTATION_ACCORD_FACULTAIRE': 'fac_approval_certificate',
    'ATTESTATION_REFUS_FACULTAIRE': 'fac_refusal_certificate',
    'ATTESTATION_ACCORD_SIC': 'sic_approval_certificate',
    'ATTESTATION_ACCORD_ANNEXE_SIC': 'sic_annexe_approval_certificate',
    'ATTESTATION_REFUS_SIC': 'sic_refusal_certificate',
}


def get_entities_with_descendants_ids(entities_acronyms):
    """
    From a list of pedagogical entities acronyms, get a set of ids of the entities and their descendants.
    :param entities_acronyms: A list of acronyms of pedagogical entities
    :return: A set of entities ids
    """
    if entities_acronyms:
        cte = (
            EntityVersion.objects.filter(acronym__in=entities_acronyms)
            .filter(Q(entity_type__in=PEDAGOGICAL_ENTITY_TYPES) | Q(acronym__in=PEDAGOGICAL_ENTITY_ADDED_EXCEPTIONS))
            .with_parents()
        )
        qs = cte.queryset().with_cte(cte).annotate(level=Func('parents', function='cardinality'))
        return set(qs.values_list('entity_id', flat=True))
    return set()
