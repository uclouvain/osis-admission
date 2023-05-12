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
from email.message import EmailMessage

from django.conf import settings
from osis_history.utilities import add_history_entry

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.domain.service.i_historique import IHistorique, PropositionAdmission
from admission.infrastructure.utils import get_message_to_historize
from base.models.person import Person
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
        gestionnaire = Person.objects.get(user__username=acteur).values('first_name', 'last_name')

        message_a_historiser = get_message_to_historize(message)

        add_history_entry(
            proposition.entity_id.uuid,
            message_a_historiser[settings.LANGUAGE_CODE_FR],
            message_a_historiser[settings.LANGUAGE_CODE_EN],
            "{first_name} {last_name}" % gestionnaire,
            tags=["proposition", "message"],
        )

        add_history_entry(
            proposition.entity_id.uuid,
            "Une demande de compléments a été envoyée par SIC.",
            "A request for additional information has been submitted by SIC.",
            acteur,
            tags=["proposition", "status-changed"],
        )

    @classmethod
    def historiser_demande_complements_fac(cls, proposition: Proposition, acteur: str, message: EmailMessage):
        gestionnaire = Person.objects.get(user__username=acteur).values('first_name', 'last_name')

        message_a_historiser = get_message_to_historize(message)

        add_history_entry(
            proposition.entity_id.uuid,
            message_a_historiser[settings.LANGUAGE_CODE_FR],
            message_a_historiser[settings.LANGUAGE_CODE_EN],
            "{first_name} {last_name}" % gestionnaire,
            tags=["proposition", "message"],
        )

        add_history_entry(
            proposition.entity_id.uuid,
            "Une demande de compléments a été envoyée par FAC.",
            "A request for additional information has been submitted by FAC.",
            acteur,
            tags=["proposition", "status-changed"],
        )
