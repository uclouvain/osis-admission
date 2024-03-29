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
import json
from typing import Dict, List, Union

import osis_document.contrib.fields
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
from admission.contrib.models.epc_injection import EPCInjectionStatus
from admission.contrib.models.general_education import AdmissionPrerequisiteCourses
from admission.ddd.admission.enums import ChoixAffiliationSport, TypeSituationAssimilation
from admission.ddd.admission.formation_generale.domain.model.enums import DROITS_INSCRIPTION_MONTANT_VALEURS
from base.models.enums.community import CommunityEnum
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.models.enums.person_address_type import PersonAddressType
from base.models.enums.sap_client_creation_source import SAPClientCreationSource
from base.models.organization import Organization
from base.models.person import Person
from base.models.person_address import PersonAddress
from osis_common.queue.queue_sender import send_message, logger
from osis_profile.models import (
    BelgianHighSchoolDiploma, ForeignHighSchoolDiploma, EducationalExperience,
    EducationalExperienceYear, ProfessionalExperience,
)
from osis_profile.models.enums.curriculum import Result, Grade
from osis_profile.models.enums.education import EducationalType, ForeignDiplomaTypes
from reference.models.diploma_title import DiplomaTitle

CODE_ETUDE_UNIV_INCONNU = '0000'
CODE_ETUDE_SNU_INCONNU = '99'
BELGIQUE_ISO_CODE = 'BE'
TYPE_DIPLOME_MAP = {
    EducationalType.TEACHING_OF_GENERAL_EDUCATION.name: 'FORMATION_GENERAL',
    EducationalType.TRANSITION_METHOD.name: 'TECHNIQUE_TRANSITION',
    EducationalType.ARTISTIC_TRANSITION.name: 'TECHNIQUE_TRANSITION',
    EducationalType.QUALIFICATION_METHOD.name: 'TECHNIQUE_QUALIFICATION',
    EducationalType.ARTISTIC_QUALIFICATION.name: 'TECHNIQUE_QUALIFICATION',
    EducationalType.PROFESSIONAL_EDUCATION.name: 'PROFESSIONNEL',
    ForeignDiplomaTypes.NATIONAL_BACHELOR.name: 'BACCALAUREAT_EUROPEEN',
    ForeignDiplomaTypes.EUROPEAN_BACHELOR.name: 'BACCALAUREAT_INTERNATIONAL',
    ForeignDiplomaTypes.INTERNATIONAL_BACCALAUREATE.name: 'BACCALAUREAT_INTERNATIONAL'
}
COMMUNAUTE_MAP = {
    CommunityEnum.FLEMISH_SPEAKING.name: 'FLAMANDE',
    CommunityEnum.GERMAN_SPEAKING.name: 'GERMANOPHONE',
    CommunityEnum.FRENCH_SPEAKING.name: 'WALLONIE_BRUXELLES',
}
RESULTAT_MAP = {
    Result.WAITING_RESULT.name: 'EN_ATTENTE_DE_RESULTAT',
    Result.SUCCESS.name: 'REUSSITE_COMPLETE',
    Result.SUCCESS_WITH_RESIDUAL_CREDITS.name: 'REUSSITE_PARTIELLE',
    Result.FAILURE.name: 'ECHEC'
}
GRADE_MAP = {
    Grade.SATISFACTION.name: 'S',
    Grade.DISTINCTION.name: 'D',
    Grade.GREAT_DISTINCTION.name: 'GD',
    Grade.GREATER_DISTINCTION.name: 'PGR',
    Grade.SUCCESS_WITHOUT_DISTINCTION.name: 'R',
    '': 'N'
}
SPORT_TOUT_CAMPUS = [
    ChoixAffiliationSport.MONS_UCL.name,
    ChoixAffiliationSport.TOURNAI_UCL.name,
    ChoixAffiliationSport.SAINT_GILLES_UCL.name,
    ChoixAffiliationSport.SAINT_LOUIS_UCL.name
]


class InjectionEPC:
    def injecter(self, admission: BaseAdmission):
        logger.info(f"[INJECTION EPC] Recuperation des donnees de l admission avec reference {str(admission)}")
        donnees = self.recuperer_donnees(admission=admission)
        EPCInjection.objects.get_or_create(
            admission=admission,
            defaults={'payload': donnees}
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
        comptabilite = getattr(admission, 'accounting', None)
        adresses = candidat.personaddress_set.select_related('country')
        adresse_domicile = adresses.filter(label=PersonAddressType.RESIDENTIAL.name).first()  # type: PersonAddress
        return {
            'dossier_uuid': str(admission.uuid),
            'signaletique': cls._get_signaletique(candidat=candidat, adresse_domicile=adresse_domicile),
            'comptabilite': cls._get_comptabilite(candidat=candidat, comptabilite=comptabilite),
            'etudes_secondaires': cls._get_etudes_secondaires(candidat=candidat, admission=admission),
            'curriculum_academique': cls._get_curriculum_academique(candidat=candidat, admission=admission),
            'curriculum_autres': cls._get_curriculum_autres_activites(candidat=candidat, admission=admission),
            'inscription_annee_academique': cls._get_inscription_annee_academique(admission=admission),
            'inscription_offre': cls._get_inscription_offre(admission=admission),
            'donnees_comptables': cls._get_donnees_comptables(admission=admission),
            'adresses': cls._get_adresses(adresses=adresses),
            'documents': cls._recuperer_documents(admission),
            'documents_manquants': cls._recuperer_documents_manquants(admission=admission)
        }

    @classmethod
    def _get_signaletique(cls, candidat: Person, adresse_domicile: PersonAddress) -> Dict:
        documents = cls._recuperer_documents(candidat)
        etudiant = candidat.student_set.first()
        return {
            'noma': etudiant.registration_id if etudiant else '',
            'nom': candidat.last_name,
            'prenom': candidat.first_name,
            'prenom_suivant': candidat.middle_name,
            'date_de_naissance': candidat.birth_date.strftime("%d/%m/%Y") if candidat.birth_date else '',
            'lieu_de_naissance': candidat.birth_place,
            'pays_de_naissance': candidat.birth_country.iso_code if candidat.birth_country else '',
            'annee_de_naissance': candidat.birth_year or '',
            'sexe': candidat.sex,
            'etat_civil': candidat.civil_state,
            'numero_gsm': candidat.phone_mobile,
            'numero_registre_national': candidat.national_number,
            'commune_domicile': adresse_domicile.place if adresse_domicile else '',
            'pays_domicile': adresse_domicile.country.iso_code if adresse_domicile else '',
            'num_carte_identite': candidat.id_card_number,
            'num_passeport': candidat.passport_number,
            'documents': documents
        }

    @staticmethod
    def _recuperer_documents(db_object) -> List[Dict[str, Union[List[str], str]]]:
        documents = []
        for field in db_object._meta.fields:
            if isinstance(field, osis_document.contrib.fields.FileField):
                files = getattr(db_object, field.name, None)
                if files:
                    documents.append({
                        'documents': [str(file) for file in files],
                        'type': field.name
                    })
        return documents

    @classmethod
    def _recuperer_documents_manquants(cls, admission: 'BaseAdmission'):
        documents = []
        for type_document, details in admission.requested_documents.items():
            documents.append({
                'type': type_document,
                'request_status': details.get('request_status')
            })
        return documents

    @classmethod
    def _get_comptabilite(cls, candidat: Person, comptabilite: Accounting) -> Dict:
        if comptabilite:
            documents = cls._recuperer_documents(comptabilite)
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
        diplome_pertinent = admission.valuated_secondary_studies_person
        if diplome_pertinent and (diplome_belge or diplome_etranger):
            diplome = diplome_belge or diplome_etranger
            documents = cls._recuperer_documents(diplome)
            type_etude = diplome_belge.educational_type if diplome_belge else diplome_etranger.foreign_diploma_type
            return {
                'osis_uuid': str(diplome.uuid),
                'type_etude': TYPE_DIPLOME_MAP.get(type_etude),
                'annee_fin': diplome.academic_graduation_year.year,
                'code_ecole': diplome_belge.institute.code if diplome_belge and diplome_belge.institute else '',
                'nom_ecole': (
                    diplome_belge.other_institute_name
                    if diplome_belge and diplome_belge.other_institute_name
                    else ''
                ),
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
                data_annuelle = cls.__build_data_annuelle(experience_educative, experience_educative_annualisee)
                experiences.append(data_annuelle)

        return experiences

    @classmethod
    def __build_data_annuelle(cls, experience_educative, experience_educative_annualisee) -> Dict:
        etablissement = experience_educative.institute  # type: Organization
        etudes = experience_educative.program  # type: DiplomaTitle
        pays_etablissement = experience_educative.country.iso_code
        communaute = etablissement.community if pays_etablissement == BELGIQUE_ISO_CODE else ''
        documents = (
            cls._recuperer_documents(experience_educative) + cls._recuperer_documents(experience_educative_annualisee)
        )

        donnees_annuelles = {
            'osis_uuid': str(experience_educative_annualisee.uuid),
            'annee_debut': experience_educative_annualisee.academic_year.year,
            'annee_fin': experience_educative_annualisee.academic_year.year + 1,
            'communaute_linguistique': COMMUNAUTE_MAP.get(communaute, ''),
            'resultat': RESULTAT_MAP.get(experience_educative_annualisee.result),
            'diplome': experience_educative.obtained_diploma,
            'intitule_etudes': experience_educative.education_name,
            'etablissement': experience_educative.institute_name,
            'adresse_etablissement': experience_educative.institute_address,
            'credits_inscrits': experience_educative_annualisee.registered_credit_number or '',
            'credits_acquis': experience_educative_annualisee.acquired_credit_number or '',
            'pays': pays_etablissement,
            'documents': documents
        }
        if etablissement and etablissement.establishment_type == EstablishmentTypeEnum.UNIVERSITY.name:
            external_id_parts = etablissement.external_id.split('_')[1:] if etablissement else []
            code_pays, code_uni, universite_id = '', '', ''
            if len(external_id_parts) > 1:
                code_pays, code_uni = external_id_parts[1:]
            elif len(external_id_parts) == 1:
                universite_id = external_id_parts[0]
            return {
                **donnees_annuelles,
                'code_etude': etudes.code_etude if etudes else CODE_ETUDE_UNIV_INCONNU,
                'type_etude': 'UNIV_BELGE' if pays_etablissement == BELGIQUE_ISO_CODE else 'UNIV_ETRG',
                'code_uni': code_uni,
                'code_pays': code_pays,
                'universite_id': universite_id,
                'grade': GRADE_MAP.get(experience_educative.obtained_grade),

            }
        return {
            **donnees_annuelles,
            'code_etude': etudes.code_etude if etudes else CODE_ETUDE_SNU_INCONNU,
            'type_etude': 'SNU_BELGE' if pays_etablissement == BELGIQUE_ISO_CODE else 'SNU_ETRG',
            'code_ecole': etablissement.code if etablissement else '',
            'type_enseignement': etablissement.teaching_type if etablissement else ''
        }

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
                'documents': cls._recuperer_documents(experience_pro),
            }
            for experience_pro in experiences_professionnelles
        ]

    @staticmethod
    def _get_inscription_annee_academique(admission: BaseAdmission) -> Dict:
        candidat = admission.candidate  # type: Person
        comptabilite = getattr(admission, 'accounting', None)  # type: Accounting
        assimilation_checklist = admission.checklist.get('current', {}).get('assimilation', {})
        return {
            'annee_academique': admission.training.academic_year.year,
            'nationalite': candidat.country_of_citizenship.iso_code if candidat.country_of_citizenship else '',
            'type_demande': admission.type_demande,
            'carte_sport_lln_woluwe': (
                comptabilite.sport_affiliation in [ChoixAffiliationSport.LOUVAIN_WOLUWE.name] + SPORT_TOUT_CAMPUS
                if comptabilite else False
            ),
            'carte_sport_mons': (
                comptabilite.sport_affiliation in [ChoixAffiliationSport.MONS.name] + SPORT_TOUT_CAMPUS
                if comptabilite else False
            ),
            'carte_sport_tournai': (
                comptabilite.sport_affiliation in [ChoixAffiliationSport.TOURNAI.name] + SPORT_TOUT_CAMPUS
                if comptabilite else False
            ),
            'carte_sport_st_louis': (
                comptabilite.sport_affiliation in [ChoixAffiliationSport.SAINT_LOUIS.name] + SPORT_TOUT_CAMPUS
                if comptabilite else False
            ),
            'carte_solidaire': comptabilite.solidarity_student or False if comptabilite else False,
            'assimilation_resident_belge': (
                comptabilite.assimilation_situation ==
                TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE.name
                if comptabilite else False
            ),
            'assimilation_refugie': (
                comptabilite.assimilation_situation ==
                TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name
                if comptabilite else False
            ),
            'assimilation_revenus': (
                comptabilite.assimilation_situation ==
                TypeSituationAssimilation.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT.name
                if comptabilite else False
            ),
            'assimilation_cpas': (
                comptabilite.assimilation_situation == TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name
                if comptabilite else False
            ),
            'assimilation_parents_ue': (
                comptabilite.assimilation_situation ==
                TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4.name
                if comptabilite else False
            ),
            'assimilation_boursier': (
                comptabilite.assimilation_situation == TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2.name
                if comptabilite else False
            ),
            'assimilation_ue': (
                comptabilite.assimilation_situation ==
                TypeSituationAssimilation.RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE.name
                if comptabilite else False
            ),
            'date_assimilation': assimilation_checklist.get('extra', {}).get('date_debut', '')
        }

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
                else ''
            ),
            'condition_acces': getattr(admission, 'admission_requirement', ''),
            'double_diplome': double_diplome.short_name if double_diplome else '',
            'type_demande_bourse': type_demande_bourse.short_name if type_demande_bourse else '',
            'type_erasmus': type_erasmus.short_name if type_erasmus else '',
            'complement_de_formation': AdmissionPrerequisiteCourses.objects.filter(admission_id=admission.id).exists(),
        }

    @staticmethod
    def _get_donnees_comptables(admission: BaseAdmission) -> Dict:
        return {
            'annee_academique': admission.training.academic_year.year,
            'droits_majores': getattr(admission, 'tuition_fees_dispensation', ''),
            'montant_doits_majores': (
                str(getattr(admission, "tuition_fees_amount_other", "")) or
                DROITS_INSCRIPTION_MONTANT_VALEURS.get(getattr(admission, "tuition_fees_amount", ""))
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
            raise InjectionVersEPCException(reference=admission_reference) from e


class InjectionVersEPCException(Exception):
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

    epc_injection = EPCInjection.objects.get(admission__uuid=dossier_uuid)
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
