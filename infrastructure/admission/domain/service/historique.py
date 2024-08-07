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
from email.message import EmailMessage
from typing import Optional

from django.conf import settings
from django.utils.translation import gettext_lazy
from osis_history.utilities import add_history_entry

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.domain.model.enums.type_gestionnaire import TypeGestionnaire
from admission.ddd.admission.domain.service.i_historique import IHistorique, PropositionAdmission
from admission.infrastructure.utils import get_message_to_historize
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import PersonneConnueUclTranslator


class Historique(IHistorique):
    @classmethod
    def historiser_initiation(cls, proposition: PropositionAdmission):
        candidat = PersonneConnueUclTranslator().get(proposition.matricule_candidat)
        add_history_entry(
            proposition.entity_id.uuid,
            "La proposition a été initiée.",
            "The proposition has been initialized.",
            "{candidat.prenom} {candidat.nom}".format(candidat=candidat),
            tags=["proposition", "status-changed"],
        )

    @classmethod
    def historiser_soumission(cls, proposition: Proposition):
        candidat = PersonneConnueUclTranslator().get(proposition.matricule_candidat)
        add_history_entry(
            proposition.entity_id.uuid,
            "La proposition a été soumise.",
            "The proposition has been submitted.",
            "{candidat.prenom} {candidat.nom}".format(candidat=candidat),
            tags=["proposition", "soumission", "status-changed"],
        )

    @classmethod
    def historiser_suppression(cls, proposition: Proposition):
        candidat = PersonneConnueUclTranslator().get(proposition.matricule_candidat)
        add_history_entry(
            proposition.entity_id.uuid,
            "La proposition a été annulée.",
            "The proposition has been cancelled.",
            "{candidat.prenom} {candidat.nom}".format(candidat=candidat),
            tags=["proposition", "status-changed"],
        )

    @classmethod
    def historiser_demande_complements_sic(cls, proposition: Proposition, acteur: str, message: EmailMessage):
        gestionnaire = PersonneConnueUclTranslator().get(acteur)

        message_a_historiser = get_message_to_historize(message)

        add_history_entry(
            proposition.entity_id.uuid,
            message_a_historiser[settings.LANGUAGE_CODE_FR],
            message_a_historiser[settings.LANGUAGE_CODE_EN],
            "{first_name} {last_name}".format(first_name=gestionnaire.prenom, last_name=gestionnaire.nom),
            tags=["proposition", "message"],
        )

        add_history_entry(
            proposition.entity_id.uuid,
            "Une demande de compléments a été envoyée par SIC.",
            "A request for additional information has been submitted by SIC.",
            "{first_name} {last_name}".format(first_name=gestionnaire.prenom, last_name=gestionnaire.nom),
            tags=["proposition", "status-changed"],
        )

    @classmethod
    def historiser_demande_complements_fac(cls, proposition: Proposition, acteur: str, message: EmailMessage):
        gestionnaire = PersonneConnueUclTranslator().get(acteur)

        message_a_historiser = get_message_to_historize(message)

        add_history_entry(
            proposition.entity_id.uuid,
            message_a_historiser[settings.LANGUAGE_CODE_FR],
            message_a_historiser[settings.LANGUAGE_CODE_EN],
            "{first_name} {last_name}".format(first_name=gestionnaire.prenom, last_name=gestionnaire.nom),
            tags=["proposition", "message"],
        )

        add_history_entry(
            proposition.entity_id.uuid,
            "Une demande de compléments a été envoyée par FAC.",
            "A request for additional information has been submitted by FAC.",
            "{first_name} {last_name}".format(first_name=gestionnaire.prenom, last_name=gestionnaire.nom),
            tags=["proposition", "status-changed"],
        )

    @classmethod
    def historiser_demande_complements(
        cls,
        proposition: Proposition,
        acteur: str,
        message: EmailMessage,
        type_gestionnaire: str = '',
    ):
        if type_gestionnaire == TypeGestionnaire.SIC.name:
            return cls.historiser_demande_complements_sic(proposition, acteur, message)
        elif type_gestionnaire == TypeGestionnaire.FAC.name:
            return cls.historiser_demande_complements_fac(proposition, acteur, message)

        gestionnaire = PersonneConnueUclTranslator().get(acteur)

        message_a_historiser = get_message_to_historize(message)

        add_history_entry(
            proposition.entity_id.uuid,
            message_a_historiser[settings.LANGUAGE_CODE_FR],
            message_a_historiser[settings.LANGUAGE_CODE_EN],
            "{first_name} {last_name}".format(first_name=gestionnaire.prenom, last_name=gestionnaire.nom),
            tags=["proposition", "message"],
        )

        add_history_entry(
            proposition.entity_id.uuid,
            "Une demande de compléments a été envoyée.",
            "A request for additional information has been submitted.",
            "{first_name} {last_name}".format(first_name=gestionnaire.prenom, last_name=gestionnaire.nom),
            tags=["proposition", "status-changed"],
        )

    @classmethod
    def historiser_completion_documents_par_candidat(cls, proposition: PropositionAdmission):
        candidat = PersonneConnueUclTranslator().get(proposition.matricule_candidat)

        add_history_entry(
            proposition.entity_id.uuid,
            "Les documents ont été complétés par le candidat.",
            "The documents have been completed by the candidate.",
            f"{candidat.prenom} {candidat.nom}",
            tags=["proposition", "status-changed"],
        )

    @classmethod
    def historiser_annulation_reclamation_documents(cls, proposition: PropositionAdmission, acteur: str, par_fac: bool):
        gestionnaire = PersonneConnueUclTranslator().get(acteur)

        actor = 'FAC' if par_fac else 'SIC'

        add_history_entry(
            proposition.entity_id.uuid,
            f"La réclamation des documents complémentaires a été annulée par {actor}.",
            f"The request for additional information has been cancelled by {actor}.",
            f"{gestionnaire.prenom} {gestionnaire.nom}",
            tags=["proposition", "status-changed"],
        )
