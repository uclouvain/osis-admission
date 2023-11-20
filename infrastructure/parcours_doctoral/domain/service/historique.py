# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from email.message import EmailMessage

from django.conf import settings

from admission.ddd.parcours_doctoral.domain.model.doctorat import Doctorat
from admission.ddd.parcours_doctoral.domain.service.i_historique import IHistorique
from admission.infrastructure.utils import get_message_to_historize
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import PersonneConnueUclTranslator
from osis_history.utilities import add_history_entry


class Historique(IHistorique):
    @classmethod
    def historiser_message_au_doctorant(cls, doctorat: Doctorat, matricule_emetteur: str, message: EmailMessage):
        emetteur = PersonneConnueUclTranslator.get(matricule_emetteur)

        message_a_historiser = get_message_to_historize(message)

        add_history_entry(
            doctorat.entity_id.uuid,
            message_a_historiser[settings.LANGUAGE_CODE_FR],
            message_a_historiser[settings.LANGUAGE_CODE_EN],
            "{emetteur.prenom} {emetteur.nom}".format(emetteur=emetteur),
            tags=["doctorat", "message"],
        )
