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
from typing import Dict

import pika
from django.conf import settings

from admission.contrib.models import Accounting, EPCInjection
from admission.contrib.models.base import (
    BaseAdmission,
)
from admission.contrib.models.epc_injection import EPCInjectionStatus, EPCInjectionType
from admission.ddd.admission.enums import ChoixAffiliationSport, TypeSituationAssimilation
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.models.person_address import PersonAddress
from base.models.person_merge_proposal import PersonMergeProposal
from osis_common.queue.queue_sender import send_message, logger
from osis_profile.services.injection_epc import InjectionEPCCurriculum

SPORT_TOUT_CAMPUS = [
    ChoixAffiliationSport.MONS_UCL.name,
    ChoixAffiliationSport.TOURNAI_UCL.name,
    ChoixAffiliationSport.SAINT_GILLES_UCL.name,
    ChoixAffiliationSport.SAINT_LOUIS_UCL.name
]


class InjectionEPCSignaletique:
    def injecter(self, admission: BaseAdmission):
        logger.info(
            f"[INJECTION EPC] Recuperation des donnees de la signaletique pour le dossier (reference {str(admission)})"
        )
        donnees = self.recuperer_donnees(admission=admission)
        EPCInjection.objects.get_or_create(
            admission=admission,
            type=EPCInjectionType.SIGNALETIQUE.name,
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
        comptabilite = getattr(admission, 'accounting', None)  # type: Accounting
        adresses = candidat.personaddress_set.select_related('country')
        adresse_domicile = adresses.filter(label=PersonAddressType.RESIDENTIAL.name).first()  # type: PersonAddress
        return {
            'dossier_uuid': str(admission.uuid),
            'signaletique': cls._get_signaletique(candidat=candidat, adresse_domicile=adresse_domicile),
            'inscription_annee_academique': cls._get_inscription_annee_academique(
                admission=admission,
                comptabilite=comptabilite,
            ),
        }

    @classmethod
    def _get_signaletique(cls, candidat: Person, adresse_domicile: PersonAddress) -> Dict:
        documents = InjectionEPCCurriculum._recuperer_documents(candidat)
        fusion = PersonMergeProposal.objects.filter(original_person=candidat).first()
        return {
            'noma': fusion.registration_id_sent_to_digit if fusion else '',
            'email': candidat.email,
            'nom': candidat.last_name,
            'prenom': candidat.first_name,
            'prenom_suivant': candidat.middle_name,
            'date_de_naissance': candidat.birth_date.strftime("%d/%m/%Y") if candidat.birth_date else None,
            'lieu_de_naissance': candidat.birth_place,
            'pays_de_naissance': candidat.birth_country.iso_code,
            'annee_de_naissance': candidat.birth_year or None,
            'sexe': candidat.sex,
            'etat_civil': candidat.civil_state,
            'numero_gsm': candidat.phone_mobile,
            'numero_registre_national': candidat.national_number,
            'commune_domicile': adresse_domicile.place,
            'pays_domicile': adresse_domicile.country.iso_code,
            'num_carte_identite': candidat.id_card_number,
            'num_passeport': candidat.passport_number,
            'documents': documents
        }

    @staticmethod
    def _get_inscription_annee_academique(admission: BaseAdmission, comptabilite: Accounting) -> Dict:
        candidat = admission.candidate  # type: Person
        assimilation_checklist = admission.checklist.get('current', {}).get('assimilation', {})
        return {
            'annee_academique': admission.training.academic_year.year,
            'nationalite': candidat.country_of_citizenship.iso_code,
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
            'date_assimilation': assimilation_checklist.get('extra', {}).get('date_debut', None)
        }

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
                f"[INJECTION EPC] Une erreur est survenue lors de l injection vers EPC de la signaletique de la demande"
                f"avec reference {admission_reference}"
            )
            raise InjectionSignaletiqueVersEPCException(reference=admission_reference) from e


class InjectionSignaletiqueVersEPCException(Exception):
    def __init__(self, reference: str, **kwargs):
        self.message = (
            f"[INJECTION EPC] Impossible d injecter la signaletique de la demande avec reference: {reference} vers EPC"
        )
        super().__init__(**kwargs)


def signaletique_response_from_epc_callback(donnees):
    donnees = json.loads(donnees.decode("utf-8").replace("\'", "\""))
    dossier_uuid, statut = donnees['dossier_uuid'], donnees['status']
    logger.info(
        f"[INJECTION EPC - RETOUR] Reception d une reponse d EPC pour la signaletique de la demande "
        f"{dossier_uuid} \nDonnees recues : {json.dumps(donnees, indent=4)}"
    )

    epc_injection = EPCInjection.objects.get(admission__uuid=dossier_uuid, type=EPCInjectionType.SIGNALETIQUE.name)
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
