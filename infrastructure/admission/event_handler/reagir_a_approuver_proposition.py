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
import contextlib
from typing import Any, Union

from admission.ddd.admission.commands import (
    RechercherCompteExistantCommand,
    ValiderTicketPersonneCommand,
    SoumettreTicketPersonneCommand,
)
from admission.ddd.admission.doctorat.events import AdmissionDoctoraleApprouveeParSicEvent
from admission.ddd.admission.doctorat.events import InscriptionDoctoraleApprouveeParSicEvent
from admission.ddd.admission.doctorat.preparation.commands import (
    EnvoyerEmailApprobationInscriptionAuCandidatCommand as EnvoyerEmailApprobationInscriptionDoctoraleAuCandidatCommand,
)
from admission.ddd.admission.formation_generale.commands import EnvoyerEmailApprobationInscriptionAuCandidatCommand
from admission.ddd.admission.formation_generale.events import (
    AdmissionApprouveeParSicEvent,
    InscriptionApprouveeParSicEvent,
)
from osis_common.ddd.interface import BusinessException


def reagir_a_approuver_proposition(
    msg_bus: Any,
    event: Union[
        'InscriptionApprouveeParSicEvent',
        'AdmissionApprouveeParSicEvent',
        'InscriptionDoctoraleApprouveeParSicEvent',
        'AdmissionDoctoraleApprouveeParSicEvent',
    ],
) -> None:
    with contextlib.suppress(BusinessException):
        msg_bus.invoke(RechercherCompteExistantCommand(matricule=event.matricule))
        msg_bus.invoke(ValiderTicketPersonneCommand(global_id=event.matricule))
        msg_bus.invoke(SoumettreTicketPersonneCommand(global_id=event.matricule))

        # The following emails contain the NOMA that can be generated just before
        if isinstance(event, InscriptionApprouveeParSicEvent):
            msg_bus.invoke(
                EnvoyerEmailApprobationInscriptionAuCandidatCommand(
                    uuid_proposition=event.entity_id.uuid,
                    objet_message=event.objet_message,
                    corps_message=event.corps_message,
                    auteur=event.auteur,
                )
            )
        elif isinstance(event, InscriptionDoctoraleApprouveeParSicEvent):
            msg_bus.invoke(
                EnvoyerEmailApprobationInscriptionDoctoraleAuCandidatCommand(
                    uuid_proposition=event.entity_id.uuid,
                    objet_message=event.objet_message,
                    corps_message=event.corps_message,
                    auteur=event.auteur,
                )
            )
