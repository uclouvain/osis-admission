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
import contextlib
from typing import Any

from admission.ddd.admission.commands import RechercherCompteExistantCommand, ValiderTicketPersonneCommand, \
    SoumettreTicketPersonneCommand
from osis_common.ddd.interface import BusinessException


def recherche_et_validation_digit(
    msg_bus: Any,
    event,
) -> None:
    with contextlib.suppress(BusinessException):
        msg_bus.invoke(RechercherCompteExistantCommand(
            matricule=event.matricule,
            nom=event.nom,
            prenom=event.prenom,
            autres_prenoms=event.autres_prenoms,
            date_naissance=event.date_naissance,
            genre=event.genre,
            niss=event.niss,
        ))
        msg_bus.invoke(ValiderTicketPersonneCommand(global_id=event.matricule))
        msg_bus.invoke(
            SoumettreTicketPersonneCommand(
                global_id=event.matricule,
                annee=event.annee,
            )
        )
