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
from typing import Dict, List

import pika
from django.conf import settings
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from admission.contrib.models import Accounting
from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.enums.actor_type import ActorType
from admission.contrib.models.general_education import AdmissionPrerequisiteCourses
from admission.ddd.admission.enums import ChoixAffiliationSport, TypeSituationAssimilation
from base.models.enums.community import CommunityEnum
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.models.enums.person_address_type import PersonAddressType
from base.models.organization import Organization
from base.models.person import Person
from base.models.person_address import PersonAddress
from osis_common.queue.queue_sender import send_message, logger
from osis_profile.models import BelgianHighSchoolDiploma, ForeignHighSchoolDiploma, EducationalExperience, \
    EducationalExperienceYear, ProfessionalExperience
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
    EducationalType.PROFESSIONAL_EDUCATION_AND_MATURITY_EXAM.name: 'PROFESSIONNEL',
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
    Result.WAITING_RESULT.name: 'PAS_DE_RESULTAT',
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
        logger.info(f"[INJECTION EPC] Recuperation des donnees de l'admission avec reference {str(admission)}")
        donnees = self.recuperer_donnees(admission=admission)
        logger.info(f"[INJECTION EPC] Donnees recuperees : {donnees} - Envoi dans la queue")
        self.envoyer_admission_dans_queue(
            donnees=donnees,
            admission_uuid=admission.uuid,
            admission_reference=str(admission)
        )
        return donnees

    def recuperer_donnees(self, admission: BaseAdmission):
        candidat = admission.candidate  # Person
        comptabilite = admission.accounting
        adresse_domicile = candidat.personaddress_set.filter(
            label=PersonAddressType.RESIDENTIAL.name
        ).select_related('country').first()  # type: PersonAddress
        return {
            'dossier_uuid': str(admission.uuid),
            'signaletique': self._get_signaletique(candidat=candidat, adresse_domicile=adresse_domicile),
            'comptabilite': self._get_comptabilite(comptabilite=comptabilite),
            'etudes_secondaires': self._get_etudes_secondaires(candidat=candidat),
            'curriculum_academique': self._get_curriculum_academique(candidat=candidat),
            'curriculum_autres': self._get_curriculum_autres_activites(candidat=candidat),
            'inscription_annee_academique': self._get_inscription_annee_academique(admission=admission),
            'inscription_offre': self._get_inscription_offre(admission=admission),
            'donnees_comptables': self._get_donnees_comptables(admission=admission),
            'adresse_domicile': self._get_adresse(adresse_domicile=adresse_domicile, numero_gsm=candidat.phone_mobile),
            # adresse contact ?
        }

    @staticmethod
    def _get_signaletique(candidat: Person, adresse_domicile: PersonAddress) -> Dict:
        return {
            'nom': candidat.last_name,
            'prenom': candidat.first_name,
            'prenom_suivant': candidat.middle_name,
            'date_de_naissance': candidat.birth_date.strftime("%d/%m/%Y") if candidat.birth_date else '',
            'lieu_de_naissance': candidat.birth_place,
            'pays_de_naissance': candidat.birth_country.iso_code,
            'annee_de_naissance': candidat.birth_year or '',
            'sexe': candidat.sex,
            'etat_civil': candidat.civil_state,
            'numero_gsm': candidat.phone_mobile,
            'numero_registre_national': candidat.national_number,
            'commune_domicile': adresse_domicile.place if adresse_domicile else '',
            'pays_domicile': adresse_domicile.country.iso_code if adresse_domicile else '',
            'num_carte_identite': candidat.id_card_number,
            'num_passeport': candidat.passport_number,
        }

    @staticmethod
    def _get_comptabilite(comptabilite: Accounting) -> Dict:
        if comptabilite:
            return {
                'iban': comptabilite.iban_account_number,
                'bic': comptabilite.bic_swift_code,
                'nom_titulaire': comptabilite.account_holder_last_name,
                'prenom_titulaire': comptabilite.account_holder_first_name
            }
        return {}

    @staticmethod
    def _get_etudes_secondaires(candidat: Person) -> Dict:
        diplome_belge = getattr(candidat, 'belgianhighschooldiploma', None)  # type: BelgianHighSchoolDiploma
        diplome_etranger = getattr(candidat, 'foreignhighschooldiploma', None)  # type: ForeignHighSchoolDiploma
        if diplome_belge or diplome_etranger:
            diplome = diplome_belge or diplome_etranger
            type_etude = diplome_belge.educational_type if diplome_belge else diplome_etranger.foreign_diploma_type
            return {
                'type_etude': TYPE_DIPLOME_MAP.get(type_etude),
                'annee_fin': diplome.academic_graduation_year.year,
                'code_ecole': diplome_belge.institute.code if diplome_belge and diplome_belge.institute else '',
                'nom_ecole': (
                    diplome_belge.other_institute_name
                    if diplome_belge and diplome_belge.other_institute_name
                    else ''
                ),
            }
        return {}

    def _get_curriculum_academique(self, candidat: Person) -> List[List[Dict]]:
        experiences_educatives = candidat.educationalexperience_set.all().select_related(
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
            experiences_annuelles = []

            for experience_educative_annualisee in experiences_educatives_annualisees:
                data_annuelle = self.__build_data_annuelle(experience_educative, experience_educative_annualisee)
                experiences_annuelles.append(data_annuelle)
            experiences.append(experiences_annuelles)

        return experiences

    @staticmethod
    def __build_data_annuelle(experience_educative, experience_educative_annualisee) -> Dict:
        etablissement = experience_educative.institute  # type: Organization
        etudes = experience_educative.program  # type: DiplomaTitle
        pays_etablissement = experience_educative.country.iso_code
        communaute = etablissement.community if pays_etablissement == BELGIQUE_ISO_CODE else ''

        donnees_annuelles = {
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
            'pays': pays_etablissement
        }
        if etablissement and etablissement.establishment_type == EstablishmentTypeEnum.UNIVERSITY.name:
            code_pays, code_uni = etablissement.external_id.split('_')[2:] if etablissement else ('', '')
            return {
                **donnees_annuelles,
                'code_etude': etudes.code_etude if etudes else CODE_ETUDE_UNIV_INCONNU,
                'type_etude': 'UNIV_BELGE' if pays_etablissement == BELGIQUE_ISO_CODE else 'UNIV_ETRG',
                'code_uni': code_uni,
                'code_pays': code_pays,
                'grade': GRADE_MAP.get(experience_educative.obtained_grade),

            }
        return {
            **donnees_annuelles,
            'code_etude': etudes.code_etude if etudes else CODE_ETUDE_SNU_INCONNU,
            'type_etude': 'SNU_BELGE' if pays_etablissement == BELGIQUE_ISO_CODE else 'SNU_ETRG',
            'code_ecole': etablissement.code if etablissement else '',
            'type_enseignement': etablissement.teaching_type if etablissement else ''
        }

    @staticmethod
    def _get_curriculum_autres_activites(candidat: Person) -> List[Dict]:
        experiences_professionnelles = candidat.professionalexperience_set.all(
        ).order_by('start_date')  # type: QuerySet[ProfessionalExperience]
        return [
            {
                'type_occupation': experience_pro.type,
                'debut': experience_pro.start_date.strftime("%d/%m/%Y"),
                'fin': experience_pro.end_date.strftime("%d/%m/%Y"),
                'type_experience_profesionnel': experience_pro.type,
                'intitule_autre_activite': experience_pro.activity,
                'etablissement_autre': experience_pro.institute_name,

            }
            for experience_pro in experiences_professionnelles
        ]

    @staticmethod
    def _get_inscription_annee_academique(admission: BaseAdmission) -> Dict:
        candidat = admission.candidate  # type: Person
        comptabilite = admission.accounting  # type: Accounting
        assimilation_checklist = admission.checklist.get('current', {}).get('assimilation', {})
        return {
            'annee_academique': admission.training.academic_year.year,
            'nationalite': candidat.country_of_citizenship.iso_code if candidat.country_of_citizenship else '',
            'type_demande': admission.type_demande,
            'carte_sport_lln_woluwe': (
                comptabilite.sport_affiliation in [ChoixAffiliationSport.LOUVAIN_WOLUWE.name] + SPORT_TOUT_CAMPUS
            ),
            'carte_sport_mons': (
                comptabilite.sport_affiliation in [ChoixAffiliationSport.MONS.name] + SPORT_TOUT_CAMPUS
            ),
            'carte_sport_tournai': (
                comptabilite.sport_affiliation in [ChoixAffiliationSport.TOURNAI.name] + SPORT_TOUT_CAMPUS
            ),
            'carte_sport_st_louis': (
                comptabilite.sport_affiliation in [ChoixAffiliationSport.SAINT_LOUIS.name] + SPORT_TOUT_CAMPUS
            ),
            'carte_solidaire': comptabilite.solidarity_student or '',
            'assimilation_resident_belge': (
                comptabilite.assimilation_situation ==
                TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE.name
            ),
            'assimilation_refugie': (
                comptabilite.assimilation_situation ==
                TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name
            ),
            'assimilation_revenus': (
                comptabilite.assimilation_situation ==
                TypeSituationAssimilation.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT.name
            ),
            'assimilation_cpas': (
                comptabilite.assimilation_situation == TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name
            ),
            'assimilation_parents_ue': (
                comptabilite.assimilation_situation ==
                TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4.name
            ),
            'assimilation_boursier': (
                comptabilite.assimilation_situation == TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2.name
            ),
            'assimilation_ue': (
                comptabilite.assimilation_situation ==
                TypeSituationAssimilation.RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE.name
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
            'condition_acces': '',  # pas encore dev
            'double_diplome': double_diplome.short_name if double_diplome else '',
            'type_demande_bourse': type_demande_bourse.short_name if type_demande_bourse else '',
            'type_erasmus': type_erasmus.short_name if type_erasmus else '',
            'complement_de_formation': AdmissionPrerequisiteCourses.objects.filter(admission_id=admission.id).exists(),
        }

    @staticmethod
    def _get_donnees_comptables(admission: BaseAdmission) -> Dict:
        return {
            'annee_academique': admission.training.academic_year.year,
            'droits_majores': '',  # pas encore dev
            'montant_doits_majores': ''  # pas encore dev
        }

    @staticmethod
    def _get_adresse(adresse_domicile: PersonAddress, numero_gsm: str) -> Dict:
        if adresse_domicile:
            return {
                'lieu_dit': adresse_domicile.place,
                'rue': (
                    f"{adresse_domicile.street}, {adresse_domicile.street_number}"
                    f"{' - ' if adresse_domicile.postal_box else ''}{adresse_domicile.postal_box}"
                ),
                'code_postal': adresse_domicile.postal_code,
                'localite': adresse_domicile.city,
                'pays': adresse_domicile.country.iso_code,
                'numero_telephone': numero_gsm
            }
        return {}

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
            logger.info()
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
                f"[INJECTION EPC] Une erreur est survenue lors de l'injection vers EPC de l'admission avec uuid "
                f"{admission_uuid} et reference {admission_reference}"
            )
            raise InjectionVersEPCException(reference=admission_reference) from e


def admission_response_from_epc_callback(donnees):
    donnees = json.loads(donnees.decode("utf-8").replace("\'", "\""))
    dossier_uuid = donnees['dossier_uuid']
    logger.info(f"[INJECTION EPC - RETOUR] Reception d'une reponse d'EPC pour l'admission avec uuid "
                f"{dossier_uuid} - Donnees recues : {donnees}")
    admission = get_object_or_404(BaseAdmission, uuid=dossier_uuid)
    if donnees['success']:
        logger.info("[INJECTION EPC - RETOUR] L'injection est terminee")
        # manage success
    else:
        logger.error(f"[INJECTION EPC - RETOUR] L'injection a echouee")
        # manage errors
    # history ?
    # notification ?


class InjectionVersEPCException(Exception):
    def __init__(self, reference: str, **kwargs):
        self.message = f"[INJECTION EPC] Impossible d'injecter l'admission avec reference: {reference} vers EPC"
        super().__init__(**kwargs)
