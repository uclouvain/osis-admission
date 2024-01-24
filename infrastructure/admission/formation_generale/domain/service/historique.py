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

import datetime
from email.message import EmailMessage
from typing import Optional

from django.conf import settings
from django.utils import formats
from osis_history.utilities import add_history_entry

from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.service.i_historique import IHistorique
from admission.infrastructure.utils import get_message_to_historize
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import PersonneConnueUclTranslator


class Historique(IHistorique):
    @classmethod
    def historiser_paiement_frais_dossier_suite_soumission(cls, proposition: Proposition):
        candidat = PersonneConnueUclTranslator().get(proposition.matricule_candidat)
        add_history_entry(
            proposition.entity_id.uuid,
            "Les frais de dossier de la proposition ont été payés suite à sa soumission.",
            "The application fee of the proposition have been paid following its submission.",
            "{candidat.prenom} {candidat.nom}".format(candidat=candidat),
            tags=["proposition", "application-fees-payment", "status-changed", "payment"],
        )

    @classmethod
    def historiser_paiement_frais_dossier_suite_demande_gestionnaire(cls, proposition: Proposition):
        candidat = PersonneConnueUclTranslator().get(proposition.matricule_candidat)
        add_history_entry(
            proposition.entity_id.uuid,
            "Les frais de dossier de la proposition ont été payés suite à une demande gestionnaire.",
            "The application fee of the proposition have been paid following a request from a manager.",
            "{candidat.prenom} {candidat.nom}".format(candidat=candidat),
            tags=["proposition", "application-fees-payment", "status-changed", "payment"],
        )

    @classmethod
    def historiser_demande_paiement_par_gestionnaire(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
        rappel: bool = False,
    ):
        gestionnaire = PersonneConnueUclTranslator().get(gestionnaire)
        message_a_historiser = get_message_to_historize(message)

        tags = ["proposition", "application-fees-payment", "request"]

        if not rappel:
            tags.append("status-changed")

        add_history_entry(
            proposition.entity_id.uuid,
            message_a_historiser[settings.LANGUAGE_CODE_FR],
            message_a_historiser[settings.LANGUAGE_CODE_EN],
            "{gestionnaire.prenom} {gestionnaire.nom}".format(gestionnaire=gestionnaire),
            tags=tags,
        )

    @classmethod
    def historiser_annulation_demande_paiement_par_gestionnaire(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        statut_initial: ChoixStatutPropositionGenerale,
    ):
        if proposition.statut == statut_initial:
            return
        gestionnaire = PersonneConnueUclTranslator().get(gestionnaire)
        add_history_entry(
            proposition.entity_id.uuid,
            "Un gestionnaire a demandé au candidat de ne pas payer des frais de dossier.",
            "A manager asked the candidate to not pay any application fee.",
            "{gestionnaire.prenom} {gestionnaire.nom}".format(gestionnaire=gestionnaire),
            tags=["proposition", "application-fees-payment", "status-changed", "cancel-request"],
        )

    @classmethod
    def historiser_envoi_fac_par_sic_lors_de_la_decision_facultaire(
        cls,
        proposition: Proposition,
        message: EmailMessage,
        gestionnaire: str,
    ):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)
        now = formats.date_format(datetime.datetime.now(), "DATETIME_FORMAT")
        recipient = message['To']
        add_history_entry(
            proposition.entity_id.uuid,
            f"Un mail informant de la soumission du dossier en faculté a été envoyé à \"{recipient}\" le {now}.",
            f"An e-mail notifying that the dossier has been submitted to the faculty was sent to "
            f"\"{recipient}\" on {now}.",
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=["proposition", "fac-decision", "send-to-fac", "status-changed"],
        )

    @classmethod
    def historiser_envoi_sic_par_fac_lors_de_la_decision_facultaire(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        envoi_par_fac: bool,
    ):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)

        if envoi_par_fac:
            message_fr = "Le dossier a été soumis au SIC par la faculté."
            message_en = "The dossier has been submitted to the SIC by the faculty."
        else:
            message_fr = "Le dossier a été soumis au SIC par le SIC."
            message_en = "The dossier has been submitted to the SIC by the SIC."

        add_history_entry(
            object_uuid=proposition.entity_id.uuid,
            message_fr=message_fr,
            message_en=message_en,
            author="{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=["proposition", "fac-decision", "send-to-sic", "status-changed"],
        )

    @classmethod
    def historiser_refus_fac(cls, proposition: Proposition, gestionnaire: PersonneConnueUclDTO):
        add_history_entry(
            proposition.entity_id.uuid,
            "La faculté a informé le SIC de son refus.",
            "The faculty informed the SIC of its refusal.",
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire),
            tags=["proposition", "fac-decision", "refusal-send-to-sic", "status-changed"],
        )

    @classmethod
    def historiser_acceptation_fac(cls, proposition: Proposition, gestionnaire: PersonneConnueUclDTO):
        add_history_entry(
            proposition.entity_id.uuid,
            "La faculté a informé le SIC de son acceptation.",
            "The faculty informed the SIC of its approval.",
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire),
            tags=["proposition", "fac-decision", "approval-send-to-sic", "status-changed"],
        )

    @classmethod
    def historiser_refus_sic(cls, proposition: Proposition, message: EmailMessage, gestionnaire: str):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)
        message_a_historiser = get_message_to_historize(message)

        add_history_entry(
            proposition.entity_id.uuid,
            message_a_historiser[settings.LANGUAGE_CODE_FR],
            message_a_historiser[settings.LANGUAGE_CODE_EN],
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=["proposition", "sic-decision", "refusal", "message"],
        )

        add_history_entry(
            proposition.entity_id.uuid,
            "Le dossier a été refusé par SIC.",
            "The dossier has been refused by SIC.",
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=["proposition", "sic-decision", "refusal", "status-changed"],
        )

    @classmethod
    def historiser_acceptation_sic(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: Optional[EmailMessage] = None,
    ):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)

        if message is not None:
            message_a_historiser = get_message_to_historize(message)

            add_history_entry(
                proposition.entity_id.uuid,
                message_a_historiser[settings.LANGUAGE_CODE_FR],
                message_a_historiser[settings.LANGUAGE_CODE_EN],
                "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
                tags=["proposition", "sic-decision", "approval", "message"],
            )

        add_history_entry(
            proposition.entity_id.uuid,
            "Le dossier a été accepté par SIC.",
            "The dossier has been accepted by SIC.",
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=["proposition", "sic-decision", "approval", "status-changed"],
        )

    @classmethod
    def historiser_specification_motifs_refus_sic(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        statut_original: ChoixStatutPropositionGenerale,
    ):
        if statut_original == proposition.statut:
            return

        gestionnaire_dto = PersonneConnueUclTranslator().get(matricule=gestionnaire)

        add_history_entry(
            proposition.entity_id.uuid,
            'Des motifs de refus ont été spécifiés par SIC.',
            'Refusal reasons have been specified by SIC.',
            '{gestionnaire_dto.prenom} {gestionnaire_dto.nom}'.format(gestionnaire_dto=gestionnaire_dto),
            tags=['proposition', 'sic-decision', 'specify-refusal-reasons', 'status-changed'],
        )

    @classmethod
    def historiser_specification_informations_acceptation_sic(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        statut_original: ChoixStatutPropositionGenerale,
    ):
        if statut_original == proposition.statut:
            return

        gestionnaire_dto = PersonneConnueUclTranslator().get(matricule=gestionnaire)

        add_history_entry(
            proposition.entity_id.uuid,
            'Des informations concernant la décision d\'acceptation ont été spécifiés par SIC.',
            'Approval decision information has been specified by SIC.',
            '{gestionnaire_dto.prenom} {gestionnaire_dto.nom}'.format(gestionnaire_dto=gestionnaire_dto),
            tags=['proposition', 'sic-decision', 'specify-approval-info', 'status-changed'],
        )
