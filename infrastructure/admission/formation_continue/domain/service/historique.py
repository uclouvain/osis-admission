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

from django.conf import settings
from django.utils import formats
from osis_history.utilities import add_history_entry

from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition
from admission.ddd.admission.formation_continue.domain.service.i_historique import IHistorique
from admission.infrastructure.utils import get_message_to_historize
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import PersonneConnueUclTranslator

TAGS_CHANGEMENT_STATUT = ["proposition", "decision", "status-changed"]
TAGS_APPROBATION_PROPOSITION = TAGS_CHANGEMENT_STATUT + ["proposition-accepted"]


class Historique(IHistorique):
    @classmethod
    def historiser_mail_decision(
        cls,
        proposition: Proposition,
        gestionnaire_dto: PersonneConnueUclDTO,
        message: EmailMessage,
    ):
        message_a_historiser = get_message_to_historize(message)

        add_history_entry(
            proposition.entity_id.uuid,
            message_a_historiser[settings.LANGUAGE_CODE_FR],
            message_a_historiser[settings.LANGUAGE_CODE_EN],
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=["proposition", "decision", "message"],
        )

    @classmethod
    def historiser_mettre_en_attente(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
    ):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)
        now = formats.date_format(datetime.datetime.now(), "DATETIME_FORMAT")

        if message:
            recipient = message['To']
            fr_message = f'Un mail informant de la mise en attente du dossier a été envoyé à "{recipient}" le {now}.'
            en_message = (
                f'An e-mail notifying that the dossier has been put on hold was sent to "{recipient}" on ' f'{now}.'
            )
            cls.historiser_mail_decision(proposition=proposition, gestionnaire_dto=gestionnaire_dto, message=message)
        else:
            fr_message = f"Le dossier a été mis en attente le {now}."
            en_message = f"The dossier has been put on hold on {now}."

        add_history_entry(
            proposition.entity_id.uuid,
            fr_message,
            en_message,
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=TAGS_CHANGEMENT_STATUT,
        )

    @classmethod
    def historiser_approuver_par_fac(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
    ):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)
        now = formats.date_format(datetime.datetime.now(), "DATETIME_FORMAT")

        if message:
            recipient = message['To']
            fr_message = (
                f'Un mail informant de l\'acceptation du dossier par la faculté a été envoyé à "{recipient}" le {now}.'
            )
            en_message = (
                f'An e-mail notifying that the dossier has been approved by the faculty was sent to "{recipient}" on '
                f'{now}.'
            )
            cls.historiser_mail_decision(proposition=proposition, gestionnaire_dto=gestionnaire_dto, message=message)
        else:
            fr_message = f"Le dossier a été accepté par la faculté le {now}."
            en_message = f"The dossier has been approved by the faculty on {now}."

        add_history_entry(
            proposition.entity_id.uuid,
            fr_message,
            en_message,
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=TAGS_CHANGEMENT_STATUT,
        )

    @classmethod
    def historiser_refuser_proposition(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
    ):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)
        now = formats.date_format(datetime.datetime.now(), "DATETIME_FORMAT")

        if message:
            recipient = message['To']
            fr_message = f'Un mail informant du refus du dossier a été envoyé à "{recipient}" le {now}.'
            en_message = f'An e-mail notifying that the dossier has been denied was sent to "{recipient}" on ' f'{now}.'
            cls.historiser_mail_decision(proposition=proposition, gestionnaire_dto=gestionnaire_dto, message=message)
        else:
            fr_message = f"Le dossier a été refusé le {now}."
            en_message = f"The dossier has been denied on {now}."

        add_history_entry(
            proposition.entity_id.uuid,
            fr_message,
            en_message,
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=TAGS_CHANGEMENT_STATUT,
        )

    @classmethod
    def historiser_annuler_proposition(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
    ):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)
        now = formats.date_format(datetime.datetime.now(), "DATETIME_FORMAT")

        if message:
            recipient = message['To']
            fr_message = f'Un mail informant de l\'annulation du dossier a été envoyé à "{recipient}" le {now}.'
            en_message = (
                f'An e-mail notifying that the dossier has been canceled was sent to "{recipient}" on ' f'{now}.'
            )
            cls.historiser_mail_decision(proposition=proposition, gestionnaire_dto=gestionnaire_dto, message=message)
        else:
            fr_message = f"Le dossier a été annulé le {now}."
            en_message = f"The dossier has been canceled on {now}."

        add_history_entry(
            proposition.entity_id.uuid,
            fr_message,
            en_message,
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=TAGS_CHANGEMENT_STATUT,
        )

    @classmethod
    def historiser_approuver_proposition(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
    ):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)
        now = formats.date_format(datetime.datetime.now(), "DATETIME_FORMAT")

        if message:
            recipient = message['To']
            fr_message = f'Un mail informant de la validation du dossier a été envoyé à "{recipient}" le {now}.'
            en_message = (
                f'An e-mail notifying that the dossier has been validated was sent to "{recipient}" on ' f'{now}.'
            )
            cls.historiser_mail_decision(proposition=proposition, gestionnaire_dto=gestionnaire_dto, message=message)
        else:
            fr_message = f"Le dossier a été validé le {now}."
            en_message = f"The dossier has been validated on {now}."

        add_history_entry(
            proposition.entity_id.uuid,
            fr_message,
            en_message,
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=TAGS_APPROBATION_PROPOSITION,
        )

    @classmethod
    def historiser_cloturer_proposition(
        cls,
        proposition: Proposition,
        gestionnaire: str,
    ):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)
        now = formats.date_format(datetime.datetime.now(), "DATETIME_FORMAT")

        add_history_entry(
            proposition.entity_id.uuid,
            f"Le dossier a été clôturé le {now}.",
            f"The dossier has been closed on {now}.",
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=TAGS_CHANGEMENT_STATUT,
        )
