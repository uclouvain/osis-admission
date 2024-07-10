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
import uuid
from typing import Dict, List

import pika
from django.conf import settings
from django.db.models import QuerySet, Case, When, Value, Exists, OuterRef

from admission.contrib.models import Accounting, EPCInjection
from admission.contrib.models.base import (
    BaseAdmission,
    AdmissionEducationalValuatedExperiences,
    AdmissionProfessionalValuatedExperiences,
)
from admission.contrib.models.enums.actor_type import ActorType
from admission.contrib.models.epc_injection import EPCInjectionStatus, EPCInjectionType
from admission.contrib.models.general_education import AdmissionPrerequisiteCourses
from admission.ddd.admission.formation_generale.domain.model.enums import DROITS_INSCRIPTION_MONTANT_VALEURS
from admission.services.injection_epc.injection_signaletique import InjectionEPCSignaletique
from base.models.enums.person_address_type import PersonAddressType
from base.models.enums.sap_client_creation_source import SAPClientCreationSource
from base.models.person import Person
from base.models.person_address import PersonAddress
from osis_common.queue.queue_sender import send_message, logger
from osis_profile import BE_ISO_CODE
from osis_profile.models import (
    BelgianHighSchoolDiploma,
    ForeignHighSchoolDiploma,
    EducationalExperience,
    EducationalExperienceYear,
    ProfessionalExperience,
    HighSchoolDiplomaAlternative,
)
from osis_profile.services.injection_epc import InjectionEPCCurriculum, TYPE_DIPLOME_MAP

DOCUMENT_MAPPING = {
    'ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT': 'INSTITUTE_ABSENCE_DEBTS_CERTIFICATE',
    'ATTESTATION_ENFANT_PERSONNEL': 'STAFF_CHILD_CERTIFICATE',
    'CARTE_RESIDENT_LONGUE_DUREE': 'LONG_TERM_RESIDENT_CARD',
    'CARTE_CIRE_SEJOUR_ILLIMITE_ETRANGER': 'CIRE_UNLIMITED_STAY_FOREIGNER_CARD',
    'CARTE_SEJOUR_MEMBRE_UE': 'UE_FAMILY_MEMBER_RESIDENCE_CARD',
    'CARTE_SEJOUR_PERMANENT_MEMBRE_UE': 'UE_FAMILY_MEMBER_PERMANENT_RESIDENCE_CARD',
    'CARTE_A_B_REFUGIE': 'REFUGEE_A_B_CARD',
    'ANNEXE_25_26_REFUGIES_APATRIDES': 'REFUGEES_STATELESS_ANNEX_25_26',
    'PREUVE_STATUT_APATRIDE': 'STATELESS_PERSON_PROOF',
    'CARTE_A_B': 'A_B_CARD',
    'DECISION_PROTECTION_SUBSIDIAIRE': 'SUBSIDIARY_PROTECTION_DECISION',
    'DECISION_PROTECTION_TEMPORAIRE': 'TEMPORARY_PROTECTION_DECISION',
    'CARTE_A': 'A_CARD',
    'TITRE_SEJOUR_3_MOIS_PROFESSIONEL': 'PROFESSIONAL_3_MONTH_RESIDENCE_PERMIT',
    'FICHES_REMUNERATION': 'SALARY_SLIPS',
    'TITRE_SEJOUR_3_MOIS_REMPLACEMENT': 'REPLACEMENT_3_MONTH_RESIDENCE_PERMIT',
    'PREUVE_ALLOCATIONS_CHOMAGE_PENSION_INDEMNITE': 'UNEMPLOYMENT_BENEFIT_PENSION_COMPENSATION_PROOF',
    'ATTESTATION_CPAS': 'CPAS_CERTIFICATE',
    'COMPOSITION_MENAGE_ACTE_NAISSANCE': 'HOUSEHOLD_COMPOSITION_OR_BIRTH_CERTIFICATE',
    'ACTE_TUTELLE': 'TUTORSHIP_ACT',
    'COMPOSITION_MENAGE_ACTE_MARIAGE': 'HOUSEHOLD_COMPOSITION_OR_MARRIAGE_CERTIFICATE',
    'ATTESTATION_COHABITATION_LEGALE': 'LEGAL_COHABITATION_CERTIFICATE',
    'CARTE_IDENTITE_PARENT': 'PARENT_IDENTITY_CARD',
    'TITRE_SEJOUR_LONGUE_DUREE_PARENT': 'PARENT_LONG_TERM_RESIDENCE_PERMIT',
    'ANNEXE_25_26_REFUGIES_APATRIDES_DECISION_PROTECTION_PARENT': (
        'PARENT_REFUGEES_STATELESS_ANNEX_25_26_OR_PROTECTION_DECISION'
    ),
    'TITRE_SEJOUR_3_MOIS_PARENT': 'PARENT_3_MONTH_RESIDENCE_PERMIT',
    'FICHES_REMUNERATION_PARENT': 'PARENT_SALARY_SLIPS',
    'ATTESTATION_CPAS_PARENT': 'PARENT_CPAS_CERTIFICATE',
    'DECISION_BOURSE_CFWB': 'CFWB_SCHOLARSHIP_DECISION',
    'ATTESTATION_BOURSIER': 'SCHOLARSHIP_CERTIFICATE',
    'TITRE_IDENTITE_SEJOUR_LONGUE_DUREE_UE': 'UE_LONG_TERM_STAY_IDENTITY_DOCUMENT',
    'TITRE_SEJOUR_BELGIQUE': 'BELGIUM_RESIDENCE_PERMIT',
    'DIPLOME_EQUIVALENCE': 'DIPLOMA_EQUIVALENCE',
    'CURRICULUM': 'CURRICULUM',
    'RELEVE_NOTES': 'TRANSCRIPT',
    'TRADUCTION_RELEVE_NOTES': 'TRANSCRIPT_TRANSLATION',
    'RELEVE_NOTES_ANNUEL': 'TRANSCRIPT_YEAR',
    'TRADUCTION_RELEVE_NOTES_ANNUEL': 'TRANSCRIPT_TRANSLATION_YEAR',
    'RESUME_MEMOIRE': 'DISSERTATION_SUMMARY',
    'DIPLOME': 'GRADUATE_DEGREE',
    'TRADUCTION_DIPLOME': 'GRADUATE_DEGREE_TRANSLATION',
    'CERTIFICAT_EXPERIENCE': 'CERTIFICATE',
    'DIPLOME_BELGE_DIPLOME': 'HIGH_SCHOOL_DIPLOMA',
    'DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_UE': 'FINAL_EQUIVALENCE_DECISION_UE',
    'DIPLOME_ETRANGER_PREUVE_DECISION_EQUIVALENCE': 'EQUIVALENCE_DECISION_PROOF',
    'DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_HORS_UE': 'FINAL_EQUIVALENCE_DECISION_NOT_UE',
    'DIPLOME_ETRANGER_DIPLOME': 'HIGH_SCHOOL_DIPLOMA',
    'DIPLOME_ETRANGER_TRADUCTION_DIPLOME': 'HIGH_SCHOOL_DIPLOMA_TRANSLATION',
    'DIPLOME_ETRANGER_RELEVE_NOTES': 'HIGH_SCHOOL_TRANSCRIPT',
    'DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES': 'HIGH_SCHOOL_TRANSCRIPT_TRANSLATION',
    'ALTERNATIVE_SECONDAIRES_EXAMEN_ADMISSION_PREMIER_CYCLE': 'FIRST_CYCLE_ADMISSION_EXAM',
    'PHOTO_IDENTITE': 'ID_PHOTO',
    'CARTE_IDENTITE': 'ID_CARD',
    'PASSEPORT': 'PASSPORT',
    'QUESTION_SPECIFIQUE': '',  # TODO
    'ADDITIONAL_DOCUMENTS': 'ADDITIONAL_DOCUMENTS',
    'COPIE_TITRE_SEJOUR': 'RESIDENCE_PERMIT',
    'ATTESTATION_INSCRIPTION_REGULIERE': 'REGULAR_REGISTRATION_PROOF',
    'FORMULAIRE_MODIFICATION_INSCRIPTION': 'REGISTRATION_CHANGE_FORM',
    'VISA_ETUDES': 'STUDENT_VISA_D',
    'AUTORISATION_PDF_SIGNEE': 'SIGNED_ENROLLMENT_AUTHORIZATION',
    'APPROBATION_PDF': '',  # TODO
    'DEMANDE_OUVERTURE': 'COTUTELLE_OPENING_REQUEST',
    'CONVENTION': 'COTUTELLE_CONVENTION',
    'AUTRES_DOCUMENTS': 'COTUTELLE_OTHER_DOCUMENTS',
    'CERTIFICAT_CONNAISSANCE_LANGUE': 'LANGUAGE_CERTIFICATE',
    'PREUVE_BOURSE': 'SCHOLARSHIP_PROOF',
    'DOCUMENTS_PROJET': 'PROJECT_DOCUMENT',
    'PROPOSITION_PROGRAMME_DOCTORAL': 'PROGRAM_PROPOSITION',
    'PROJET_FORMATION_COMPLEMENTAIRE': 'ADDITIONAL_TRAINING_PROJECT',
    'GRAPHE_GANTT': 'GANTT_GRAPH',
    'LETTRES_RECOMMANDATION': 'RECOMMENDATION_LETTERS',
    'LIBRE_CANDIDAT': 'CANDIDATE_FREE'
}


class InjectionEPCAdmission:
    def injecter(self, admission: BaseAdmission):
        logger.info(f"[INJECTION EPC] Recuperation des donnees de l admission avec reference {str(admission)}")
        donnees = self.recuperer_donnees(admission=admission)
        EPCInjection.objects.get_or_create(
            admission=admission,
            type=EPCInjectionType.DEMANDE.name,
            defaults={'payload': donnees, 'status': EPCInjectionStatus.PENDING.name}
        )
        logger.info(f"[INJECTION EPC] Donnees recuperees : {json.dumps(donnees, indent=4)} - Envoi dans la queue")
        logger.info(f"[INJECTION EPC] Envoi dans la queue ...")
        self.envoyer_admission_dans_queue(
            donnees=donnees,
            admission_uuid=admission.uuid,
            admission_reference=str(admission)
        )
        return donnees

    @classmethod
    def recuperer_donnees(cls, admission: BaseAdmission):
        candidat = admission.candidate  # Person
        comptabilite = getattr(admission, 'accounting', None) # type: Accounting
        adresses = candidat.personaddress_set.select_related('country')
        adresse_domicile = adresses.filter(label=PersonAddressType.RESIDENTIAL.name).first()  # type: PersonAddress
        return {
            'dossier_uuid': str(admission.uuid),
            'signaletique': InjectionEPCSignaletique._get_signaletique(
                candidat=candidat,
                adresse_domicile=adresse_domicile,
            ),
            'comptabilite': cls._get_comptabilite(candidat=candidat, comptabilite=comptabilite),
            'etudes_secondaires': cls._get_etudes_secondaires(candidat=candidat, admission=admission),
            'curriculum_academique': cls._get_curriculum_academique(candidat=candidat, admission=admission),
            'curriculum_autres': cls._get_curriculum_autres_activites(candidat=candidat, admission=admission),
            'inscription_annee_academique': InjectionEPCSignaletique._get_inscription_annee_academique(
                admission=admission,
                comptabilite=comptabilite
            ),
            'inscription_offre': cls._get_inscription_offre(admission=admission),
            'donnees_comptables': cls._get_donnees_comptables(admission=admission),
            'adresses': cls._get_adresses(adresses=adresses),
            'documents': InjectionEPCCurriculum._recuperer_documents(admission),
            'documents_manquants': cls._recuperer_documents_manquants(admission=admission)
        }

    @classmethod
    def _recuperer_documents_manquants(cls, admission: 'BaseAdmission'):
        documents = []
        for type_document_compose, details in admission.requested_documents.items():
            annee, type_document, uuid_experience = (
                cls._recuperer_informations_utiles_documents_manquants(type_document_compose)
            )
            documents.append({
                'type': DOCUMENT_MAPPING.get(type_document, f"Fail-{type_document}"),
                'annee_academique': annee,
                'curex_uuid': uuid_experience,
                'request_status': details.get('request_status')
            })
        return documents

    @classmethod
    def _recuperer_informations_utiles_documents_manquants(cls, type_document_compose):
        type_document, annee, uuid_experience = '', '', ''
        parties_type_document = type_document_compose.split('.')
        if parties_type_document[0] == 'LIBRE_CANDIDAT':
            # type_document_compose = LIBRE_CANDIDAT.uuid
            type_document = parties_type_document[0]
        elif len(parties_type_document) == 2:
            # type_document_compose = ONGLET.TYPE_DOCUMENT
            type_document = parties_type_document[1]
        elif cls.__est_uuid_valide(parties_type_document[-1]):
            # type_document_compose = ONGLET.TYPE_DOCUMENT.uuid (Questions spécifiques)
            _, type_document, uuid_question = parties_type_document[1]
        elif len(parties_type_document) == 3:
            # type_document_compose = ONGLET.uuid.TYPE_DOCUMENT
            _, uuid_experience, type_document = parties_type_document[-1]
        else:
            # type_document_compose = ONGLET.uuid.annee.TYPE_DOCUMENT (Annuel)
            _, uuid_experience, annee, type_document = parties_type_document
        if uuid_experience:
            uuid_experience = EducationalExperienceYear.objects.filter(
                educational_experience__uuid=uuid_experience,
            ).latest('academic_year__year').uuid
        return annee, type_document, str(uuid_experience)

    @staticmethod
    def __est_uuid_valide(chaine):
        try:
            uuid.UUID(chaine)
            return True
        except ValueError:
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
                'client_sap': client_sap.client_number if client_sap else '',
                'iban': comptabilite.iban_account_number,
                'bic': comptabilite.bic_swift_code,
                'nom_titulaire': comptabilite.account_holder_last_name,
                'prenom_titulaire': comptabilite.account_holder_first_name,
                'documents': documents
            }
        return {}

    @classmethod
    def _get_etudes_secondaires(cls, candidat: Person, admission: BaseAdmission) -> Dict:
        diplome_belge = getattr(candidat, 'belgianhighschooldiploma', None)  # type: BelgianHighSchoolDiploma
        diplome_etranger = getattr(candidat, 'foreignhighschooldiploma', None)  # type: ForeignHighSchoolDiploma
        alternative = getattr(candidat, 'highschooldiplomaalternative', None)  # type: HighSchoolDiplomaAlternative
        connaissances_en_langues = candidat.languages_knowledge.all()
        diplome_pertinent = admission.valuated_secondary_studies_person
        if (diplome_pertinent and (diplome_belge or diplome_etranger)) or alternative or connaissances_en_langues:
            diplome = diplome_belge or diplome_etranger
            documents = (InjectionEPCCurriculum._recuperer_documents(diplome) if diplome else []) + (
                InjectionEPCCurriculum._recuperer_documents(alternative) if alternative else []
            ) + [{
                'documents': [str(file) for langue in connaissances_en_langues for file in langue.certificate],
                'type':'LANGUAGE_CERTIFICATE',
            }]
            type_etude = diplome_belge.educational_type if diplome_belge else diplome_etranger.foreign_diploma_type
            return {
                'osis_uuid': str(diplome.uuid) if diplome else '',
                'type_etude': TYPE_DIPLOME_MAP.get(type_etude),
                'annee_fin': diplome.academic_graduation_year.year if diplome else '',
                'code_ecole': diplome_belge.institute.code if diplome_belge and diplome_belge.institute else None,
                'nom_ecole': (
                    diplome_belge.other_institute_name
                    if diplome_belge and diplome_belge.other_institute_name
                    else None
                ),
                'code_pays': diplome_etranger.country.iso_code if diplome_etranger else BE_ISO_CODE,
                'documents': documents
            }
        return {}

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
            experiences_educatives_annualisees = experience_educative.educationalexperienceyear_set.all(

            ).select_related(
                'academic_year',
            ).order_by(
                'academic_year'
            )  # type: QuerySet[EducationalExperienceYear]

            for experience_educative_annualisee in experiences_educatives_annualisees:
                data_annuelle = InjectionEPCCurriculum._build_data_annuelle(experience_educative, experience_educative_annualisee)
                experiences.append(data_annuelle)

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
            {
                'osis_uuid': str(experience_pro.uuid),
                'type_occupation': experience_pro.type,
                'debut': experience_pro.start_date.strftime("%d/%m/%Y"),
                'fin': experience_pro.end_date.strftime("%d/%m/%Y"),
                'intitule_autre_activite': experience_pro.activity,
                'etablissement_autre': experience_pro.institute_name,
                'documents': InjectionEPCCurriculum._recuperer_documents(experience_pro),
            }
            for experience_pro in experiences_professionnelles
        ]

    @staticmethod
    def _get_inscription_offre(admission: BaseAdmission) -> Dict:
        validite, num_offre = admission.training.external_id.split('_')[4:6]
        groupe_de_supervision = getattr(admission, 'supervision_group', None)
        double_diplome = getattr(admission, 'double_degree_scholarship', None)
        type_demande_bourse = getattr(admission, 'international_scholarship', None)
        type_erasmus = getattr(admission, 'erasmus_mundus_scholarship', None)
        return {
            'num_offre': num_offre,
            'validite': validite,
            'promoteur': (
                groupe_de_supervision.actors.get(supervisionactor__type=ActorType.PROMOTER.name).person.global_id
                if groupe_de_supervision
                else None
            ),
            'condition_acces': getattr(admission, 'admission_requirement', None),
            'double_diplome': str(double_diplome.uuid) if double_diplome else None,
            'type_demande_bourse': str(type_demande_bourse.uuid) if type_demande_bourse else None,
            'type_erasmus': str(type_erasmus.uuid) if type_erasmus else None,
            'complement_de_formation': AdmissionPrerequisiteCourses.objects.filter(admission_id=admission.id).exists(),
        }

    @staticmethod
    def _get_donnees_comptables(admission: BaseAdmission) -> Dict:
        return {
            'annee_academique': admission.training.academic_year.year,
            'droits_majores': getattr(admission, 'tuition_fees_dispensation', None),
            'montant_doits_majores': (
                str(getattr(admission, "tuition_fees_amount_other", "")) or
                DROITS_INSCRIPTION_MONTANT_VALEURS.get(getattr(admission, "tuition_fees_amount", None))
            )
        }

    @staticmethod
    def _get_adresses(adresses: QuerySet[PersonAddress]) -> List[Dict[str, str]]:
        if adresses:
            return [
                {
                    'lieu_dit': adresse.place,
                    'rue': (
                        f"{adresse.street}, {adresse.street_number}"
                        f"{' - ' if adresse.postal_box else ''}{adresse.postal_box}"
                    ),
                    'code_postal': adresse.postal_code,
                    'localite': adresse.city,
                    'pays': adresse.country.iso_code,
                    'type': adresse.label
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
            settings.QUEUES.get('QUEUE_URL'),
            settings.QUEUES.get('QUEUE_PORT'),
            settings.QUEUES.get('QUEUE_CONTEXT_ROOT'),
            credentials
        )
        try:
            connect = pika.BlockingConnection(rabbit_settings)
            channel = connect.channel()
            queue_name = settings.QUEUES.get('QUEUES_NAME').get('ADMISSION_TO_EPC')
            send_message(queue_name, donnees, connect, channel)
            # change something in admission object ? epc_injection_status ? = sended
            # history ?
            # notification ?
        except (
            RuntimeError,
            pika.exceptions.ConnectionClosed,
            pika.exceptions.ChannelClosed,
            pika.exceptions.AMQPError
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
    donnees = json.loads(donnees.decode("utf-8").replace("\'", "\""))
    dossier_uuid, statut = donnees['dossier_uuid'], donnees['status']
    logger.info(
        f"[INJECTION EPC - RETOUR] Reception d une reponse d EPC pour l admission avec uuid "
        f"{dossier_uuid} \nDonnees recues : {json.dumps(donnees, indent=4)}"
    )

    epc_injection = EPCInjection.objects.get(admission__uuid=dossier_uuid, type=EPCInjectionType.DEMANDE.name)
    epc_injection.status = statut
    epc_injection.epc_responses.append(donnees)
    epc_injection.save()

    if statut == EPCInjectionStatus.OK.name:
        logger.info("[INJECTION EPC - RETOUR] L injection a ete effectuee avec succes")
    else:
        erreurs = [f"\t- {erreur['message']}" for erreur in donnees['errors']]
        logger.error(f"[INJECTION EPC - RETOUR] L injection a echouee pour ce/ces raison(s) : \n" + "\n".join(erreurs))
    # history ?
    # notification ?
