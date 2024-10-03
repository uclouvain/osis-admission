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

import json
import re
import traceback
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import pika
from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet, Case, When, Value, Exists, OuterRef
from unidecode import unidecode

from admission.constants import CONTEXT_CONTINUING, CONTEXT_DOCTORATE, CONTEXT_GENERAL
from admission.contrib.models import Accounting, EPCInjection, AdmissionFormItem
from admission.contrib.models import GeneralEducationAdmission
from admission.contrib.models.base import (
    BaseAdmission,
    AdmissionEducationalValuatedExperiences,
    AdmissionProfessionalValuatedExperiences,
)
from admission.contrib.models.categorized_free_document import CategorizedFreeDocument
from admission.contrib.models.enums.actor_type import ActorType
from admission.contrib.models.epc_injection import EPCInjectionStatus, EPCInjectionType
from admission.ddd.admission.doctorat.preparation.commands import (
    RecalculerEmplacementsDocumentsNonLibresPropositionCommand as
    RecalculerEmplacementsDocumentsNonLibresDoctoratCommand
)
from admission.ddd.admission.enums import TypeItemFormulaire
from admission.ddd.admission.formation_continue.commands import (
    RecalculerEmplacementsDocumentsNonLibresPropositionCommand as RecalculerEmplacementsDocumentsNonLibresIUFCCommand
)
from admission.ddd.admission.formation_generale.commands import (
    RecalculerEmplacementsDocumentsNonLibresPropositionCommand as RecalculerEmplacementsDocumentsNonLibresGeneralCommand
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    DROITS_INSCRIPTION_MONTANT_VALEURS, PoursuiteDeCycle,
)
from admission.infrastructure.utils import (
    CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_NON_ACADEMIQUE,
)
from admission.services.injection_epc.injection_signaletique import (
    InjectionEPCSignaletique,
)
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType
from base.models.enums.person_address_type import PersonAddressType
from base.models.enums.sap_client_creation_source import SAPClientCreationSource
from base.models.person import Person
from base.models.person_address import PersonAddress
from ddd.logic.financabilite.domain.model.enums.etat import EtatFinancabilite
from education_group.models.enums.cohort_name import CohortName
from infrastructure.messages_bus import message_bus_instance
from osis_common.queue.queue_sender import send_message, logger
from osis_profile.models import (
    EducationalExperience,
    EducationalExperienceYear,
    ProfessionalExperience,
)
from osis_profile.services.injection_epc import InjectionEPCCurriculum

DOCUMENT_MAPPING = {
    "ACTE_DE_TUTELLE": "TUTORSHIP_ACT",
    "ACTE_TUTELLE": "TUTORSHIP_ACT",
    "ADDITIONAL_DOCUMENTS": "ADDITIONAL_DOCUMENTS",
    "ALTERNATIVE_SECONDAIRES_EXAMEN_ADMISSION_PREMIER_CYCLE": "FIRST_CYCLE_ADMISSION_EXAM",
    "ANNEXE_25_26_REFUGIES_APATRIDES": "REFUGEES_STATELESS_ANNEX_25_26",
    "ANNEXE_25_26_REFUGIES_APATRIDES_DECISION_PROTECTION_PARENT": (
        "PARENT_REFUGEES_STATELESS_ANNEX_25_26_OR_PROTECTION_DECISION"
    ),
    "ANNEXE_25_OU_26": "REFUGEES_STATELESS_ANNEX_25_26",
    "ANNEXE_25_OU_26_-_ASSIMILATION_5_(FAMILLE)": "PARENT_REFUGEES_STATELESS_ANNEX_25_26_OR_PROTECTION_DECISION",
    "APPROBATION_PDF": "PDF_FROM_CANDIDATE",
    "ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT": "INSTITUTE_ABSENCE_DEBTS_CERTIFICATE",
    "ATTESTATION_ACCORD_ANNEXE_SIC": "SIC_ANNEXE_APPROVAL_CERTIFICATE",
    "ATTESTATION_ACCORD_FACULTAIRE": "FAC_APPROVAL_CERTIFICATE",
    "ATTESTATION_ACCORD_SIC": "SIC_APPROVAL_CERTIFICATE",
    "ATTESTATION_BOURSIER": "SCHOLARSHIP_CERTIFICATE",
    "ATTESTATION_COHABITATION_LEGALE": "LEGAL_COHABITATION_CERTIFICATE",
    "ATTESTATION_CPAS": "CPAS_CERTIFICATE",
    "ATTESTATION_CPAS_PARENT": "PARENT_CPAS_CERTIFICATE",
    "ATTESTATION_DE_COHABITATION_LEGALE": "LEGAL_COHABITATION_CERTIFICATE",
    "ATTESTATION_ENFANT_DU_PERSONNEL": "STAFF_CHILD_CERTIFICATE",
    "ATTESTATION_ENFANT_PERSONNEL": "STAFF_CHILD_CERTIFICATE",
    "ATTESTATION_IMMATRICULATION": "REGISTRATION_CERTIFICATE",
    "ATTESTATION_INSCRIPTION_REGULIERE": "REGULAR_REGISTRATION_PROOF",
    "ATTESTATION_PRISE_EN_CHARGE_CPAS": "CPAS_CERTIFICATE",
    "ATTESTATION_PRISE_EN_CHARGE_CPAS_(FAMILLE)": "PARENT_CPAS_CERTIFICATE",
    "ATTESTATION_REFUS_FACULTAIRE": "FAC_REFUSAL_CERTIFICATE",
    "ATTESTATION_REFUS_SIC": "SIC_REFUSAL_CERTIFICATE",
    "AUTORISATION_PDF_SIGNEE": "SIGNED_ENROLLMENT_AUTHORIZATION",
    "AUTRES_DOCUMENTS": "COTUTELLE_OTHER_DOCUMENTS",
    "CARTE_A": "A_CARD",
    "CARTE_A_B": "A_B_CARD",
    "CARTE_A_B_REFUGIE": "REFUGEE_A_B_CARD",
    "CARTE_A_OU_B": "A_B_CARD",
    "CARTE_CIRE_SEJOUR_ILLIMITE_ETRANGER": "CIRE_UNLIMITED_STAY_FOREIGNER_CARD",
    "CARTE_D'IDENTITE": "ID_CARD",
    "CARTE_D'IDENTITE_-_ASSIMILATION_5_(FAMILLE)": "PARENT_IDENTITY_CARD",
    "CARTE_IDENTITE": "ID_CARD",
    "CARTE_IDENTITE_PARENT": "PARENT_IDENTITY_CARD",
    "CARTE_RESIDENT_LONGUE_DUREE": "LONG_TERM_RESIDENT_CARD",
    "CARTE_SEJOUR_MEMBRE_UE": "UE_FAMILY_MEMBER_RESIDENCE_CARD",
    "CARTE_SEJOUR_PERMANENT_MEMBRE_UE": "UE_FAMILY_MEMBER_PERMANENT_RESIDENCE_CARD",
    "CERTIFICAT_CONNAISSANCE_LANGUE": "LANGUAGE_CERTIFICATE",  # Ou certificate ?
    "CERTIFICAT_EXPERIENCE": "CERTIFICATE",
    "COMPOSITION_DE_MENAGE_OU_ACTE_DE_MARIAGE": "HOUSEHOLD_COMPOSITION_OR_MARRIAGE_CERTIFICATE",
    "COMPOSITION_DE_MENAGE_OU_ACTE_DE_NAISSANCE": "HOUSEHOLD_COMPOSITION_OR_BIRTH_CERTIFICATE",
    "COMPOSITION_MENAGE_ACTE_MARIAGE": "HOUSEHOLD_COMPOSITION_OR_MARRIAGE_CERTIFICATE",
    "COMPOSITION_MENAGE_ACTE_NAISSANCE": "HOUSEHOLD_COMPOSITION_OR_BIRTH_CERTIFICATE",
    "CONVENTION": "COTUTELLE_CONVENTION",
    "COPIE_TITRE_SEJOUR": "RESIDENCE_PERMIT",
    "CURRICULUM": "CURRICULUM",
    "CURRICULUM_VITAE_DETAILLE_DATE_ET_SIGNE": "CURRICULUM",
    "DECISION_BOURSE_CFWB": "CFWB_SCHOLARSHIP_DECISION",
    "DECISION_PROTECTION_SUBSIDIAIRE": "SUBSIDIARY_PROTECTION_DECISION",
    "DECISION_PROTECTION_TEMPORAIRE": "TEMPORARY_PROTECTION_DECISION",
    "DEMANDE_OUVERTURE": "COTUTELLE_OPENING_REQUEST",
    "DIPLOME": "GRADUATE_DEGREE",
    "DIPLOME_BELGE_DIPLOME": "HIGH_SCHOOL_DIPLOMA",
    "DIPLOME_D'ETUDES_SECONDAIRES": "HIGH_SCHOOL_DIPLOMA",
    "DIPLOME_EQUIVALENCE": "DIPLOMA_EQUIVALENCE",
    "DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_HORS_UE": "FINAL_EQUIVALENCE_DECISION_NOT_UE",
    "DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_UE": "FINAL_EQUIVALENCE_DECISION_UE",
    "DIPLOME_ETRANGER_DIPLOME": "HIGH_SCHOOL_DIPLOMA",
    "DIPLOME_ETRANGER_PREUVE_DECISION_EQUIVALENCE": "EQUIVALENCE_DECISION_PROOF",
    "DIPLOME_ETRANGER_RELEVE_NOTES": "HIGH_SCHOOL_TRANSCRIPT",
    "DIPLOME_ETRANGER_TRADUCTION_DIPLOME": "HIGH_SCHOOL_DIPLOMA_TRANSLATION",
    "DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES": "HIGH_SCHOOL_TRANSCRIPT_TRANSLATION",
    "DOCUMENTS_PROJET": "PROJECT_DOCUMENT",
    "DOSSIER_ANALYSE": "PDF_RECAP",
    "FICHES_DE_PAIE_-_ASSIMILATION_5_(PARENTS,...)": "PARENT_SALARY_SLIPS",
    "FICHES_REMUNERATION": "SALARY_SLIPS",
    "FICHES_REMUNERATION_PARENT": "PARENT_SALARY_SLIPS",
    "FORMULAIRE_MODIFICATION_INSCRIPTION": "REGISTRATION_CHANGE_FORM",
    "GRAPHE_GANTT": "GANTT_GRAPH",
    "LETTRES_RECOMMANDATION": "RECOMMENDATION_LETTERS",
    "LIBRE_CANDIDAT": "CANDIDATE_FREE",
    "PASSEPORT": "PASSPORT",
    "PHOTO_D'IDENTITE": "ID_PHOTO",
    "PHOTO_IDENTITE": "ID_PHOTO",
    "PREUVE_ALLOCATIONS_CHOMAGE_PENSION_INDEMNITE": "UNEMPLOYMENT_BENEFIT_PENSION_COMPENSATION_PROOF",
    "PREUVE_BOURSE": "SCHOLARSHIP_PROOF",
    "PREUVE_DU_STATUT_D'APATRIDE": "STATELESS_PERSON_PROOF",
    "PREUVE_STATUT_APATRIDE": "STATELESS_PERSON_PROOF",
    "PROJET_FORMATION_COMPLEMENTAIRE": "ADDITIONAL_TRAINING_PROJECT",
    "PROPOSITION_PROGRAMME_DOCTORAL": "PROGRAM_PROPOSITION",
    "QUESTION_SPECIFIQUE": "",  # TODO
    "RELEVE_DE_NOTES_(PLUSIEURS_ANNEES)": "TRANSCRIPT",
    "RELEVE_DE_NOTES_(UNE_SEULE_ANNEE)": "TRANSCRIPT_YEAR",
    "RELEVE_DE_NOTES_D'ETUDES_SECONDAIRES": "HIGH_SCHOOL_TRANSCRIPT",
    "RELEVE_NOTES": "TRANSCRIPT",
    "RELEVE_NOTES_ANNUEL": "TRANSCRIPT_YEAR",
    "RESUME_MEMOIRE": "DISSERTATION_SUMMARY",
    "TITRE_DE_SEJOUR_-_ASSIMILATION_5_(ASSIMILATION_5)": "PARENT_LONG_TERM_RESIDENCE_PERMIT",
    "TITRE_DE_SEJOUR_BELGE": "BELGIUM_RESIDENCE_PERMIT",
    "TITRE_DE_SEJOUR_LONGUE_DUREE_-_ASSIMILATION_5_(FAMILLE)": "PARENT_3_MONTH_RESIDENCE_PERMIT",
    "TITRE_IDENTITE_SEJOUR_LONGUE_DUREE_UE": "UE_LONG_TERM_STAY_IDENTITY_DOCUMENT",
    "TITRE_SEJOUR_3_MOIS_PARENT": "PARENT_3_MONTH_RESIDENCE_PERMIT",
    "TITRE_SEJOUR_3_MOIS_PROFESSIONEL": "PROFESSIONAL_3_MONTH_RESIDENCE_PERMIT",
    "TITRE_SEJOUR_3_MOIS_REMPLACEMENT": "REPLACEMENT_3_MONTH_RESIDENCE_PERMIT",
    "TITRE_SEJOUR_BELGIQUE": "BELGIUM_RESIDENCE_PERMIT",
    "TITRE_SEJOUR_LONGUE_DUREE_PARENT": "PARENT_LONG_TERM_RESIDENCE_PERMIT",
    "TRADUCITION_DU_DIPLOME_D'ETUDES_SECONDAIRES": "HIGH_SCHOOL_DIPLOMA_TRANSLATION",
    "TRADUCTION_DIPLOME": "GRADUATE_DEGREE_TRANSLATION",
    "TRADUCTION_DU_DIPLOME": "GRADUATE_DEGREE_TRANSLATION",
    "TRADUCTION_DU_RELEVE_DE_NOTES_(PLUSIEURS_ANNEES)": "TRANSCRIPT_TRANSLATION",
    "TRADUCTION_DU_RELEVE_DE_NOTES_(UNE_SEULE_ANNEE)": "TRANSCRIPT_TRANSLATION_YEAR",
    "TRADUCTION_DU_RELEVE_DE_NOTES_D'ETUDES_SECONDAIRES": "HIGH_SCHOOL_TRANSCRIPT_TRANSLATION",
    "TRADUCTION_RELEVE_NOTES": "TRANSCRIPT_TRANSLATION",
    "TRADUCTION_RELEVE_NOTES_ANNUEL": "TRANSCRIPT_TRANSLATION_YEAR",
    "VISA_D'ETUDES": "STUDENT_VISA_D",
    "VISA_ETUDES": "STUDENT_VISA_D"
}


class InjectionEPCAdmission:
    def injecter(self, admission: BaseAdmission):
        logger.info(f"[INJECTION EPC] Recuperation des donnees de l admission avec reference {str(admission)}")
        e = ""
        try:
            self._nettoyer_documents_reclames(admission)
            donnees = self.recuperer_donnees(admission=admission)
            logger.info(f"[INJECTION EPC] Donnees recuperees : {json.dumps(donnees, indent=4)} - Envoi dans la queue")
            logger.info("[INJECTION EPC] Envoi dans la queue ...")
            transaction.on_commit(
                lambda: self.envoyer_admission_dans_queue(
                    donnees=donnees,
                    admission_uuid=admission.uuid,
                    admission_reference=str(admission),
                )
            )
            statut = EPCInjectionStatus.PENDING.name
        except Exception as exception:
            e = exception
            logger.exception("[INJECTION EPC] Erreur lors de l'injection")
            donnees = {}
            statut = EPCInjectionStatus.OSIS_ERROR.name
            stacktrace = traceback.format_exc()

        EPCInjection.objects.update_or_create(
            admission=admission,
            type=EPCInjectionType.DEMANDE.name,
            defaults={
                "payload": donnees,
                "status": statut,
                'last_attempt_date': datetime.now(),
                "osis_error_message": str(e) if e else "",
                "osis_stacktrace": stacktrace if e else ""
            },
        )
        return donnees

    @staticmethod
    def _nettoyer_documents_reclames(admission):
        logger.info("[INJECTION EPC] Nettoyage des documents reclames plus necessaires")
        commands = {
            CONTEXT_GENERAL: RecalculerEmplacementsDocumentsNonLibresGeneralCommand,
            CONTEXT_CONTINUING: RecalculerEmplacementsDocumentsNonLibresIUFCCommand,
            CONTEXT_DOCTORATE: RecalculerEmplacementsDocumentsNonLibresDoctoratCommand
        }
        RecalculerEmplacementsDocumentsNonLibresCommand = commands[admission.get_admission_context()]
        message_bus_instance.invoke(
            RecalculerEmplacementsDocumentsNonLibresCommand(uuid_proposition=admission.uuid)
        )
        admission.refresh_from_db(fields=['requested_documents'])

    @classmethod
    def recuperer_donnees(cls, admission: BaseAdmission):
        candidat = admission.candidate  # Person
        comptabilite = getattr(admission, "accounting", None)  # type: Accounting
        adresses = candidat.personaddress_set.select_related("country").exclude(
            label=PersonAddressType.PROFESSIONAL.name,
        )
        adresse_domicile = adresses.filter(label=PersonAddressType.RESIDENTIAL.name).first()  # type: PersonAddress
        etudes_secondaires, alternative = cls._get_etudes_secondaires(candidat=candidat, admission=admission)
        admission_generale = getattr(admission, 'generaleducationadmission', None)
        admission_iufc = getattr(admission, 'continuingeducationadmission', None)
        documents_specifiques = cls._recuperer_documents_specifiques(admission)
        return {
            "dossier_uuid": str(admission.uuid),
            "signaletique": InjectionEPCSignaletique._get_signaletique(
                candidat=candidat,
                adresse_domicile=adresse_domicile,
            ),
            "comptabilite": cls._get_comptabilite(candidat=candidat, comptabilite=comptabilite),
            "etudes_secondaires": etudes_secondaires,
            "curriculum_academique": cls._get_curriculum_academique(candidat=candidat, admission=admission),
            "curriculum_autres": (
                cls._get_curriculum_autres_activites(candidat=candidat, admission=admission)
                + ([alternative] if alternative else [])
            ),
            "inscription_annee_academique": InjectionEPCSignaletique._get_inscription_annee_academique(
                admission=admission,
                comptabilite=comptabilite,
            ),
            "inscription_offre": cls._get_inscription_offre(admission=admission, admission_generale=admission_generale),
            "donnees_comptables": cls._get_donnees_comptables(
                admission=admission,
                comptabilite=comptabilite,
                admission_generale=admission_generale
            ),
            "adresses": cls._get_adresses(adresses=adresses),
            "documents": (
                InjectionEPCCurriculum._recuperer_documents(admission_generale or admission_iufc)
                +
                documents_specifiques
            ),
            "documents_manquants": cls._recuperer_documents_manquants(admission=admission),
        }

    @classmethod
    def _recuperer_documents_specifiques(cls, admission):
        documents_specifiques = []
        form_items = AdmissionFormItem.objects.filter(
            uuid__in=admission.specific_question_answers.keys(),
            type=TypeItemFormulaire.DOCUMENT.name
        )
        for form_item in form_items:
            label = form_item.internal_label.lower()
            if cls.__contient_uuid_valide(label):
                document = CategorizedFreeDocument.objects.filter(long_label_fr=form_item.title['fr-be']).first()
                label = document.short_label_fr.lower() if document else "Label du document non trouve"
            documents_specifiques.append({
                "type": re.sub(r'[\W_]+', '_', unidecode(label)).strip('_'),
                "documents": admission.specific_question_answers[str(form_item.uuid)]
            })
        return documents_specifiques

    @classmethod
    def _recuperer_documents_manquants(cls, admission: "BaseAdmission"):
        documents = []
        for type_document_compose, details in admission.requested_documents.items():
            if details.get('request_status'):
                annee, label_document, uuid_experience = (
                    cls._recuperer_informations_utiles_documents_manquants(type_document_compose)
                )
                type_document = DOCUMENT_MAPPING.get(label_document, "CANDIDATE_FREE")
                documents.append(
                    {
                        "type": type_document,
                        "label": label_document if type_document == 'CANDIDATE_FREE' else "",
                        "annee_academique": annee,
                        "curex_uuid": uuid_experience,
                        "request_status": details.get("request_status"),
                    }
                )
        return documents

    @classmethod
    def _recuperer_informations_utiles_documents_manquants(cls, type_document_compose):
        type_document, annee, uuid_experience = "", "", ""
        parties_type_document = type_document_compose.split(".")
        if parties_type_document[0] == "LIBRE_CANDIDAT":
            # type_document_compose = LIBRE_CANDIDAT.uuid
            uuid_question = parties_type_document[1]
            question = AdmissionFormItem.objects.get(uuid=uuid_question)
            document = CategorizedFreeDocument.objects.filter(
                long_label_en__in=[
                    question.title['en'],
                    f"{question.title['en'].split(':')[0]}: " + "{annee_academique}"
                ]
            ).first()
            type_document = (
                unidecode(document.short_label_fr.replace(' ', '_').upper())
                if document
                else unidecode(question.title['en'].replace(' ', '_'))
            )
        elif len(parties_type_document) == 2:
            # type_document_compose = ONGLET.TYPE_DOCUMENT
            type_document = parties_type_document[1]
        elif cls.__contient_uuid_valide(parties_type_document[-1]):
            # type_document_compose = ONGLET.TYPE_DOCUMENT.uuid (Questions spécifiques)
            _, type_document, uuid_question = parties_type_document
        elif len(parties_type_document) == 3:
            # type_document_compose = ONGLET.uuid.TYPE_DOCUMENT
            _, uuid_experience, type_document = parties_type_document
        else:
            # type_document_compose = ONGLET.uuid.annee.TYPE_DOCUMENT (Annuel)
            _, uuid_experience, annee, type_document = parties_type_document
        if uuid_experience and type_document not in CORRESPONDANCE_CHAMPS_CURRICULUM_EXPERIENCE_NON_ACADEMIQUE:
            uuid_experience = EducationalExperienceYear.objects.filter(
                educational_experience__uuid=uuid_experience,
            ).latest('academic_year__year').uuid
        elif uuid_experience:
            uuid_experience = ProfessionalExperience.objects.get(uuid=uuid_experience).uuid
        return annee, type_document, str(uuid_experience)

    @staticmethod
    def __contient_uuid_valide(chaine):
        uuid_regex = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
        match = re.search(uuid_regex, chaine)
        if match:
            try:
                uuid.UUID(match.group(0))
                return True
            except ValueError:
                return False
        return False

    @classmethod
    def _get_comptabilite(cls, candidat: Person, comptabilite: Accounting) -> Dict:
        if comptabilite:
            documents = InjectionEPCCurriculum._recuperer_documents(comptabilite)
            client_sap = candidat.sapclient_set.annotate(
                priorite=Case(
                    When(creation_source=SAPClientCreationSource.OSIS.name), then=Value(1),
                    default=2
                )
            ).order_by('priorite').first()
            return {
                "client_sap": client_sap.client_number if client_sap else "",
                "iban": comptabilite.iban_account_number,
                "bic": comptabilite.bic_swift_code,
                "nom_titulaire": comptabilite.account_holder_last_name,
                "prenom_titulaire": comptabilite.account_holder_first_name,
                "documents": documents,
            }
        return {}

    @classmethod
    def _get_etudes_secondaires(cls, candidat: Person, admission: BaseAdmission) -> Tuple[Dict, Dict]:
        _, etudes_secondaires = InjectionEPCCurriculum._get_etudes_secondaires(personne=candidat)
        _, alternative = InjectionEPCCurriculum._get_alternative_etudes_secondaires(personne=candidat)
        return etudes_secondaires or None, alternative or None

    @classmethod
    def _get_curriculum_academique(cls, candidat: Person, admission: BaseAdmission) -> List[Dict]:
        experiences_educatives = candidat.educationalexperience_set.annotate(
            valorisee_par_dossier=Exists(
                AdmissionEducationalValuatedExperiences.objects.filter(
                    baseadmission_id=admission.uuid,
                    educationalexperience_id=OuterRef('uuid')
                )
            )
        ).filter(
            valorisee_par_dossier=True
        ).select_related(
            'institute',
            'country',
            'program'
        )  # type: QuerySet[EducationalExperience]
        experiences = []

        for experience_educative in experiences_educatives:
            experiences_educatives_annualisees = (
                experience_educative.educationalexperienceyear_set.all()
                .select_related("academic_year")
                .order_by("academic_year")
            )  # type: QuerySet[EducationalExperienceYear]
            exp = []
            for experience_educative_annualisee in experiences_educatives_annualisees:
                data_annuelle = InjectionEPCCurriculum._build_data_annuelle(
                    experience_educative,
                    experience_educative_annualisee,
                )
                exp.append(data_annuelle)
            exp[-1].update({'diplome': experience_educative.obtained_diploma})
            experiences += exp
        return experiences

    @classmethod
    def _get_curriculum_autres_activites(cls, candidat: Person, admission: BaseAdmission) -> List[Dict]:
        experiences_professionnelles = candidat.professionalexperience_set.annotate(
            valorisee_par_dossier=Exists(
                AdmissionProfessionalValuatedExperiences.objects.filter(
                    baseadmission_id=admission.uuid,
                    professionalexperience_id=OuterRef('uuid')
                )
            )
        ).filter(
            valorisee_par_dossier=True
        ).order_by('start_date')  # type: QuerySet[ProfessionalExperience]

        return [
            InjectionEPCCurriculum._build_curriculum_autre_activite(experience_pro)
            for experience_pro in experiences_professionnelles
        ]

    @classmethod
    def _get_inscription_offre(
        cls,
        admission: BaseAdmission,
        admission_generale: Optional[GeneralEducationAdmission],
    ) -> Dict:
        num_offre, validite = cls.__get_validite_num_offre(admission, admission_generale)
        groupe_de_supervision = getattr(admission, 'supervision_group', None)
        double_diplome = getattr(admission_generale, 'double_degree_scholarship', None)
        type_demande_bourse = getattr(admission_generale, 'international_scholarship', None)
        type_erasmus = getattr(admission_generale, 'erasmus_mundus_scholarship', None)
        financabilite_checklist = admission.checklist.get('current', {}).get('financabilite', {})
        return {
            "num_offre": num_offre,
            "validite": validite,
            "promoteur": (
                groupe_de_supervision.actors.get(supervisionactor__type=ActorType.PROMOTER.name).person.global_id
                if groupe_de_supervision
                else None
            ),
            'condition_acces': admission_generale.admission_requirement if admission_generale else None,
            'annee_condition_acces': admission_generale.admission_requirement_year.year if admission_generale else None,
            'double_diplome': str(double_diplome.uuid) if double_diplome else None,
            'type_demande_bourse': str(type_demande_bourse.uuid) if type_demande_bourse else None,
            'type_erasmus': str(type_erasmus.uuid) if type_erasmus else None,
            'complement_de_formation': admission_generale.with_prerequisite_courses if admission_generale else False,
            'etat_financabilite': {
                'INITIAL_NON_CONCERNE': EtatFinancabilite.NON_CONCERNE.name,
                'GEST_REUSSITE': EtatFinancabilite.FINANCABLE.name
            }.get(financabilite_checklist.get('statut')),
            'situation_financabilite': admission_generale.financability_rule if admission_generale else None,
            'utilisateur_financabilite': (
                admission_generale.financability_rule_established_by.full_name if admission_generale else None
            ),
            'date_financabilite': (
                admission_generale.financability_rule_established_on.strftime("%d/%m/%Y")
                if admission_generale else None
            ),
            'derogation_financabilite': financabilite_checklist.get('extra', {}).get('reussite') == 'derogation',
            'reorientation': bool(admission_generale) and admission_generale.is_external_reorientation,
            'modification_programme': bool(admission_generale) and admission_generale.is_external_modification,
            'inscription_tardive': bool(admission_generale) and admission_generale.late_enrollment,
        }

    @staticmethod
    def __get_validite_num_offre(
        admission: BaseAdmission,
        admission_generale: Optional[GeneralEducationAdmission],
    ) -> Tuple[str, str]:
        formation = admission.training  # type: EducationGroupYear
        est_en_bachelier = formation.education_group_type.name == TrainingType.BACHELOR.name
        est_en_premiere_annee_de_bachelier = (
            est_en_bachelier and admission_generale.cycle_pursuit != PoursuiteDeCycle.YES.name
        )
        if est_en_premiere_annee_de_bachelier:
            validite, num_offre = formation.cohortyear_set.get(
                name=CohortName.FIRST_YEAR.name,
            ).external_id.split('_')[3:5]
        else:
            validite, num_offre = formation.external_id.split('_')[4:6]
        return num_offre, validite

    @staticmethod
    def _get_donnees_comptables(
        admission: BaseAdmission,
        comptabilite: Accounting,
        admission_generale: Optional[GeneralEducationAdmission],
    ) -> Dict:
        autre_montant = getattr(admission_generale, 'tuition_fees_amount_other')
        return {
            "annee_academique": admission.training.academic_year.year,
            "droits_majores": admission_generale.tuition_fees_dispensation,
            "montant_droits_majores": (
                ((str(autre_montant) if autre_montant else None)
                 or DROITS_INSCRIPTION_MONTANT_VALEURS.get(getattr(admission_generale, "tuition_fees_amount", None)))
                if admission_generale else None
            ),
            "allocation_etudes": comptabilite.french_community_study_allowance_application if comptabilite else None,
        }

    @staticmethod
    def _get_adresses(adresses: QuerySet[PersonAddress]) -> List[Dict[str, str]]:
        if adresses:
            return [
                {
                    "lieu_dit": adresse.place,
                    "rue": str(adresse),
                    "code_postal": adresse.postal_code,
                    "localite": adresse.city,
                    "pays": adresse.country.iso_code,
                    "type": adresse.label,
                }
                for adresse in adresses
            ]
        return []

    @staticmethod
    def envoyer_admission_dans_queue(donnees: Dict, admission_uuid: str, admission_reference: str):
        credentials = pika.PlainCredentials(
            settings.QUEUES.get('QUEUE_USER'),
            settings.QUEUES.get('QUEUE_PASSWORD')
        )
        rabbit_settings = pika.ConnectionParameters(
            settings.QUEUES.get("QUEUE_URL"),
            settings.QUEUES.get("QUEUE_PORT"),
            settings.QUEUES.get("QUEUE_CONTEXT_ROOT"),
            credentials,
        )
        try:
            connect = pika.BlockingConnection(rabbit_settings)
            channel = connect.channel()
            queue_name = settings.QUEUES.get("QUEUES_NAME").get("ADMISSION_TO_EPC")
            send_message(queue_name, donnees, connect, channel)
            # change something in admission object ? epc_injection_status ? = sended
            # history ?
            # notification ?
        except (
            RuntimeError,
            pika.exceptions.ConnectionClosed,
            pika.exceptions.ChannelClosed,
            pika.exceptions.AMQPError,
        ) as e:
            logger.exception(
                f"[INJECTION EPC] Une erreur est survenue lors de l injection vers EPC de l admission avec uuid "
                f"{admission_uuid} et reference {admission_reference}"
            )
            raise InjectionDemandeVersEPCException(reference=admission_reference) from e


class InjectionDemandeVersEPCException(Exception):
    def __init__(self, reference: str, **kwargs):
        self.message = f"[INJECTION EPC] Impossible d injecter l admission avec reference: {reference} vers EPC"
        super().__init__(**kwargs)


def admission_response_from_epc_callback(donnees):
    donnees = json.loads(donnees.decode("utf-8"))
    dossier_uuid, statut = donnees["dossier_uuid"], donnees["status"]
    logger.info(
        f"[INJECTION EPC - RETOUR] Reception d une reponse d EPC pour l admission avec uuid "
        f"{dossier_uuid} \nDonnees recues : {json.dumps(donnees, indent=4)}"
    )

    epc_injection = EPCInjection.objects.get(admission__uuid=dossier_uuid, type=EPCInjectionType.DEMANDE.name)
    epc_injection.status = statut
    epc_injection.epc_responses.append(donnees)
    epc_injection.last_response_date = datetime.now()
    epc_injection.save()

    if statut == EPCInjectionStatus.OK.name:
        logger.info("[INJECTION EPC - RETOUR] L injection a ete effectuee avec succes")
    else:
        erreurs = [f"\t- {erreur['message']}" for erreur in donnees["errors"]]
        logger.error(f"[INJECTION EPC - RETOUR] L injection a echouee pour ce/ces raison(s) : \n" + "\n".join(erreurs))
    # history ?
    # notification ?
