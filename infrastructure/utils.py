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
import uuid

import attr

from admission.constants import UUID_COMPILE_REGEX
from admission.contrib.models import (
    SupervisionActor,
)
from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.enums.emplacement_document import (
    DocumentsInterOnglets,
    OngletsDemande,
    DocumentsIdentification,
    DocumentsEtudesSecondaires,
    DocumentsConnaissancesLangues,
    DocumentsCurriculum,
    DocumentsQuestionsSpecifiques,
    DocumentsComptabilite,
    DocumentsProjetRecherche,
    DocumentsCotutelle,
    DocumentsSupervision,
    TypeDocument,
)
from osis_profile.models import EducationalExperienceYear


def dto_to_dict(dto):
    """Make a shallow dict copy of a DTO."""
    return dict((field.name, getattr(dto, field.name)) for field in attr.fields(type(dto)))


def get_document_from_identifier(
    admission: BaseAdmission,
    document_identifier: str,
):
    """
    Get the document uuid from the document identifier and a specific admission.
    The identifier is composed of:
    - [TAB_IDENTIFIER].QUESTION_SPECIFIQUE.[SPECIFIC_QUESTION_UUID] for a specific question or a requested free document
    - DOCUMENTS_ADDITIONNELS.[DOCUMENT_UUID] for free documents uploaded by a manager
    - DOCUMENTS_ADDITIONNELS.[DOCUMENT_IDENTIFIER] for internal documents that are generated by the system
    - [TAB_IDENTIFIER].[DOCUMENT_IDENTIFIER] for categorized documents. If a document belongs to a model different from
    the admission then the related object uuid is included between the tab and the document identifiers.
    """
    field = None
    obj = None
    document_type = None
    document_uuids = []
    requestable_document = None
    document_identifier_parts = document_identifier.split('.')
    identifiers_nb = len(document_identifier_parts)
    requested_document = admission.requested_documents.get(document_identifier, {})

    if identifiers_nb < 2:
        return

    tab = document_identifier_parts[0]

    if document_identifier_parts[1] == DocumentsInterOnglets.QUESTION_SPECIFIQUE.name:
        # [TAB_IDENTIFIER].QUESTION_SPECIFIQUE.[SPECIFIC_QUESTION_UUID]
        # Question specific documents (requested free documents or previously defined questions)
        if identifiers_nb != 3:
            return
        obj = admission
        field = 'specific_question_answers'
        document_uuids = admission.specific_question_answers.get(document_identifier_parts[2])
        document_type = requested_document.get('type', TypeDocument.NON_LIBRE.name)
        requestable_document = True

    elif tab == OngletsDemande.DOCUMENTS_ADDITIONNELS.name:
        # Additional documents
        obj = admission
        requestable_document = False

        if UUID_COMPILE_REGEX.fullmatch(document_identifier_parts[1]):
            # Free documents uploaded by the manager
            # DOCUMENTS_ADDITIONNELS.[DOCUMENT_UUID]
            document_uuid = uuid.UUID(document_identifier_parts[1])
            field = next(
                (
                    field
                    for field in [
                        'fac_documents',
                        'sic_documents',
                        'uclouvain_sic_documents',
                        'uclouvain_fac_documents',
                    ]
                    if document_uuid in getattr(admission, field)
                ),
                None,
            )
            document_uuids = [document_uuid]
            document_type = {
                'fac_documents': TypeDocument.CANDIDAT_FAC.name,
                'sic_documents': TypeDocument.CANDIDAT_SIC.name,
                'uclouvain_sic_documents': TypeDocument.INTERNE_SIC.name,
                'uclouvain_fac_documents': TypeDocument.INTERNE_FAC.name,
            }[field]

        elif hasattr(DocumentsInterOnglets, document_identifier_parts[1]):
            # System documents
            # DOCUMENTS_ADDITIONNELS.[DOCUMENT_IDENTIFIER]
            document_type = TypeDocument.SYSTEME.name
            if document_identifier_parts[1] == DocumentsInterOnglets.DOSSIER_ANALYSE.name:
                obj = admission
                field = 'pdf_recap'
                document_uuids = admission.pdf_recap

    # Categorized documents
    else:
        document_type = TypeDocument.NON_LIBRE.name
        requestable_document = True
        field = document_identifier_parts[-1]
        if tab == OngletsDemande.IDENTIFICATION.name:
            # IDENTIFICATION.[DOCUMENT_IDENTIFIER]
            obj = admission.candidate
            field = CORRESPONDANCE_CHAMPS_IDENTIFICATION.get(field)

        elif tab == OngletsDemande.ETUDES_SECONDAIRES.name:
            # ETUDES_SECONDAIRES.[DOCUMENT_IDENTIFIER]
            if field in CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_BELGES:
                obj = getattr(admission.candidate, 'belgianhighschooldiploma', None)
                field = CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_BELGES.get(field)
            elif field in CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_BELGES:
                obj = getattr(admission.candidate, 'foreignhighschooldiploma', None)
                field = CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_BELGES.get(field)
            elif field in CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_BELGES:
                obj = getattr(admission.candidate, 'highschooldiplomaalternative', None)
                field = CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_BELGES.get(field)

        elif tab == OngletsDemande.LANGUES.name:
            # LANGUES.[CODE_LANGUE].[DOCUMENT_IDENTIFIER]
            if not identifiers_nb == 3:
                return
            language_code = document_identifier_parts[1]
            obj = admission.candidate.languages_knowledge.filter(language__code=language_code).first()
            field = CORRESPONDANCE_CHAMPS_CONNAISSANCES_LANGUES.get(field)

        elif tab == OngletsDemande.CURRICULUM.name:
            if field in CORRESPONDANCE_CHAMPS_CURRICULUM_BASE:
                # CURRICULUM.[DOCUMENT_IDENTIFIER]
                obj = admission
                field = CORRESPONDANCE_CHAMPS_CURRICULUM_BASE.get(field)

            elif field in CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_ACADEMIQUE:
                # CURRICULUM.[EXPERIENCE_UUID].[DOCUMENT_IDENTIFIER]
                if not identifiers_nb == 3:
                    return
                experience_uuid = document_identifier_parts[1]
                field = CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_ACADEMIQUE.get(field)
                obj = admission.candidate.educationalexperience_set.filter(uuid=experience_uuid).first()

            elif field in CORRESPONDANCE_CHAMPS_CURRICULUM_ANNEE_EXPERIENCE_ACADEMIQUE:
                # CURRICULUM.[EXPERIENCE_UUID].[EXPERIENCE_YEAR].[DOCUMENT_IDENTIFIER]
                if not identifiers_nb == 4:
                    return
                experience_uuid = document_identifier_parts[1]
                experience_year = document_identifier_parts[2]
                field = CORRESPONDANCE_CHAMPS_CURRICULUM_ANNEE_EXPERIENCE_ACADEMIQUE.get(field)
                obj = EducationalExperienceYear.objects.filter(
                    educational_experience__uuid=experience_uuid,
                    academic_year__year=experience_year,
                ).first()

            elif field in CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_NON_ACADEMIQUE:
                # CURRICULUM.[EXPERIENCE_UUID].[DOCUMENT_IDENTIFIER]
                if not identifiers_nb == 3:
                    return
                experience_uuid = document_identifier_parts[1]
                field = CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_NON_ACADEMIQUE.get(field)
                obj = admission.candidate.professionalexperience_set.filter(uuid=experience_uuid).first()

        elif tab == OngletsDemande.INFORMATIONS_ADDITIONNELLES.name:
            # INFORMATIONS_ADDITIONNELLES.[DOCUMENT_IDENTIFIER]
            obj = admission
            field = CORRESPONDANCE_CHAMPS_INFORMATIONS_ADDITIONNELLES.get(field)

        elif tab == OngletsDemande.COMPTABILITE.name:
            # COMPTABILITE.[DOCUMENT_IDENTIFIER]
            obj = admission.accounting
            field = CORRESPONDANCE_CHAMPS_COMPTABILITE.get(field)

        elif tab == OngletsDemande.PROJET.name:
            # PROJET.[DOCUMENT_IDENTIFIER]
            obj = admission
            field = CORRESPONDANCE_CHAMPS_PROJET.get(field)

        elif tab == OngletsDemande.COTUTELLE.name:
            # COTUTELLE.[DOCUMENT_IDENTIFIER]
            obj = admission
            field = CORRESPONDANCE_CHAMPS_COTUTELLE.get(field)

        elif tab == OngletsDemande.SUPERVISION.name:
            # SUPERVISION.[ACTOR_UUID].[DOCUMENT_IDENTIFIER]
            if not identifiers_nb == 3:
                return
            actor_uuid = document_identifier_parts[1]
            obj = SupervisionActor.objects.filter(uuid=actor_uuid).first()
            field = CORRESPONDANCE_CHAMPS_SUPERVISION.get(field)

        if obj and field:
            document_uuids = getattr(obj, field, [])

    if obj and field and document_type:
        return {
            'obj': obj,
            'field': field,
            'uuids': document_uuids,
            'type': document_type,
            'requestable': requestable_document,
        }


CORRESPONDANCE_CHAMPS_IDENTIFICATION = {
    DocumentsIdentification.PASSEPORT.name: 'passport',
    DocumentsIdentification.CARTE_IDENTITE.name: 'id_card',
    DocumentsIdentification.PHOTO_IDENTITE.name: 'id_photo',
}

CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_BELGES = {
    DocumentsEtudesSecondaires.DIPLOME_BELGE_DIPLOME.name: 'high_school_diploma',
    DocumentsEtudesSecondaires.DIPLOME_BELGE_CERTIFICAT_INSCRIPTION.name: 'enrolment_certificate',
}

CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_ETRANGERES = {
    DocumentsEtudesSecondaires.DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_UE.name: 'final_equivalence_decision_ue',
    DocumentsEtudesSecondaires.DIPLOME_ETRANGER_PREUVE_DECISION_EQUIVALENCE.name: 'equivalence_decision_proof',
    DocumentsEtudesSecondaires.DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_HORS_UE.name: 'final_equivalence_decision_not_ue',
    DocumentsEtudesSecondaires.DIPLOME_ETRANGER_DIPLOME.name: 'high_school_diploma',
    DocumentsEtudesSecondaires.DIPLOME_ETRANGER_TRADUCTION_DIPLOME.name: 'high_school_diploma_translation',
    DocumentsEtudesSecondaires.DIPLOME_ETRANGER_CERTIFICAT_INSCRIPTION.name: 'enrolment_certificate',
    DocumentsEtudesSecondaires.DIPLOME_ETRANGER_TRADUCTION_CERTIFICAT_INSCRIPTION.name: 'enrolment_certificate_translation',
    DocumentsEtudesSecondaires.DIPLOME_ETRANGER_RELEVE_NOTES.name: 'high_school_transcript',
    DocumentsEtudesSecondaires.DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES.name: 'high_school_transcript_translation',
}

CORRESPONDANCE_CHAMPS_ETUDES_SECONDAIRES_ALTERNATIVES = {
    DocumentsEtudesSecondaires.ALTERNATIVE_SECONDAIRES_EXAMEN_ADMISSION_PREMIER_CYCLE.name: 'first_cycle_admission_exam',
}

CORRESPONDANCE_CHAMPS_CONNAISSANCES_LANGUES = {
    DocumentsConnaissancesLangues.CERTIFICAT_CONNAISSANCE_LANGUE.name: 'certificate',
}

CORRESPONDANCE_CHAMPS_CURRICULUM_BASE = {
    DocumentsCurriculum.DIPLOME_EQUIVALENCE.name: 'diploma_equivalence',
    DocumentsCurriculum.CURRICULUM.name: 'curriculum',
}

CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_ACADEMIQUE = {
    DocumentsCurriculum.RELEVE_NOTES.name: 'transcript',
    DocumentsCurriculum.TRADUCTION_RELEVE_NOTES.name: 'transcript_translation',
    DocumentsCurriculum.RESUME_MEMOIRE.name: 'dissertation_summary',
    DocumentsCurriculum.DIPLOME.name: 'graduate_degree',
    DocumentsCurriculum.TRADUCTION_DIPLOME.name: 'graduate_degree_translation',
}

CORRESPONDANCE_CHAMPS_CURRICULUM_ANNEE_EXPERIENCE_ACADEMIQUE = {
    DocumentsCurriculum.RELEVE_NOTES_ANNUEL.name: 'transcript',
    DocumentsCurriculum.TRADUCTION_RELEVE_NOTES_ANNUEL.name: 'transcript_translation',
}

CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_NON_ACADEMIQUE = {
    DocumentsCurriculum.CERTIFICAT_EXPERIENCE.name: 'certificate',
}

CORRESPONDANCE_CHAMPS_INFORMATIONS_ADDITIONNELLES = {
    DocumentsQuestionsSpecifiques.COPIE_TITRE_SEJOUR.name: 'residence_permit',
    DocumentsQuestionsSpecifiques.ATTESTATION_INSCRIPTION_REGULIERE.name: 'regular_registration_proof',
    DocumentsQuestionsSpecifiques.FORMULAIRE_MODIFICATION_INSCRIPTION.name: 'registration_change_form',
}

CORRESPONDANCE_CHAMPS_COMPTABILITE = {
    DocumentsComptabilite.ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT.name: 'institute_absence_debts_certificate',
    DocumentsComptabilite.ATTESTATION_ENFANT_PERSONNEL.name: 'is_staff_child',
    DocumentsComptabilite.CARTE_RESIDENT_LONGUE_DUREE.name: 'long_term_resident_card',
    DocumentsComptabilite.CARTE_CIRE_SEJOUR_ILLIMITE_ETRANGER.name: 'cire_unlimited_stay_foreigner_card',
    DocumentsComptabilite.CARTE_SEJOUR_MEMBRE_UE.name: 'ue_family_member_residence_card',
    DocumentsComptabilite.CARTE_SEJOUR_PERMANENT_MEMBRE_UE.name: 'ue_family_member_permanent_residence_card',
    DocumentsComptabilite.CARTE_A_B_REFUGIE.name: 'refugee_a_b_card',
    DocumentsComptabilite.ANNEXE_25_26_REFUGIES_APATRIDES.name: 'refugees_stateless_annex_25_26',
    DocumentsComptabilite.ATTESTATION_IMMATRICULATION.name: 'registration_certificate',
    DocumentsComptabilite.CARTE_A_B.name: 'a_b_card',
    DocumentsComptabilite.DECISION_PROTECTION_SUBSIDIAIRE.name: 'subsidiary_protection_decision',
    DocumentsComptabilite.DECISION_PROTECTION_TEMPORAIRE.name: 'temporary_protection_decision',
    DocumentsComptabilite.TITRE_SEJOUR_3_MOIS_PROFESSIONEL.name: 'professional_3_month_residence_permit',
    DocumentsComptabilite.FICHES_REMUNERATION.name: 'salary_slips',
    DocumentsComptabilite.TITRE_SEJOUR_3_MOIS_REMPLACEMENT.name: 'replacement_3_month_residence_permit',
    DocumentsComptabilite.PREUVE_ALLOCATIONS_CHOMAGE_PENSION_INDEMNITE.name: 'unemployment_benefit_pension_compensation_proof',
    DocumentsComptabilite.ATTESTATION_CPAS.name: 'cpas_certificate',
    DocumentsComptabilite.COMPOSITION_MENAGE_ACTE_NAISSANCE.name: 'household_composition_or_birth_certificate',
    DocumentsComptabilite.ACTE_TUTELLE.name: 'tutorship_act',
    DocumentsComptabilite.COMPOSITION_MENAGE_ACTE_MARIAGE.name: 'household_composition_or_marriage_certificate',
    DocumentsComptabilite.ATTESTATION_COHABITATION_LEGALE.name: 'legal_cohabitation_certificate',
    DocumentsComptabilite.CARTE_IDENTITE_PARENT.name: 'parent_identity_card',
    DocumentsComptabilite.TITRE_SEJOUR_LONGUE_DUREE_PARENT.name: 'parent_long_term_residence_permit',
    DocumentsComptabilite.ANNEXE_25_26_REFUGIES_APATRIDES_DECISION_PROTECTION_PARENT.name: 'parent_refugees_stateless_annex_25_26_or_protection_decision',
    DocumentsComptabilite.TITRE_SEJOUR_3_MOIS_PARENT.name: 'parent_3_month_residence_permit',
    DocumentsComptabilite.FICHES_REMUNERATION_PARENT.name: 'parent_salary_slips',
    DocumentsComptabilite.ATTESTATION_CPAS_PARENT.name: 'parent_cpas_certificate',
    DocumentsComptabilite.DECISION_BOURSE_CFWB.name: 'cfwb_scholarship_decision',
    DocumentsComptabilite.ATTESTATION_BOURSIER.name: 'scholarship_certificate',
    DocumentsComptabilite.TITRE_IDENTITE_SEJOUR_LONGUE_DUREE_UE.name: 'ue_long_term_stay_identity_document',
    DocumentsComptabilite.TITRE_SEJOUR_BELGIQUE.name: 'belgium_residence_permit',
}

CORRESPONDANCE_CHAMPS_PROJET = {
    DocumentsProjetRecherche.PREUVE_BOURSE.name: 'scholarship_proof',
    DocumentsProjetRecherche.DOCUMENTS_PROJET.name: 'project_document',
    DocumentsProjetRecherche.PROPOSITION_PROGRAMME_DOCTORAL.name: 'program_proposition',
    DocumentsProjetRecherche.PROJET_FORMATION_COMPLEMENTAIRE.name: 'additional_training_project',
    DocumentsProjetRecherche.GRAPHE_GANTT.name: 'gantt_graph',
    DocumentsProjetRecherche.LETTRES_RECOMMANDATION.name: 'recommendation_letters',
}

CORRESPONDANCE_CHAMPS_COTUTELLE = {
    DocumentsCotutelle.DEMANDE_OUVERTURE.name: 'cotutelle_opening_request',
    DocumentsCotutelle.CONVENTION.name: 'cotutelle_convention',
    DocumentsCotutelle.AUTRES_DOCUMENTS.name: 'cotutelle_other_documents',
}

CORRESPONDANCE_CHAMPS_SUPERVISION = {
    DocumentsSupervision.APPROBATION_PDF.name: 'pdf_from_candidate',
}
