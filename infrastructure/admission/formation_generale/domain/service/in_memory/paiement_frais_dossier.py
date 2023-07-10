##############################################################################
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
##############################################################################
from typing import List

import attr

from admission.ddd.admission.formation_generale.domain.service.i_paiement_frais_dossier import IPaiementFraisDossier


@attr.dataclass
class Paiement:
    uuid_proposition: str
    effectue: bool = False


class PaiementFraisDossierInMemory(IPaiementFraisDossier):
    paiements: List[Paiement] = []

    @classmethod
    def reset(cls):
        cls.paiements = [
            Paiement(uuid_proposition='uuid-MASTER-SCI-CONFIRMED', effectue=False),
            Paiement(uuid_proposition='uuid-MASTER-SCI', effectue=False),
        ]

    @classmethod
    def paiement_realise(cls, proposition_uuid: str) -> bool:
        return any(
            paiement
            for paiement in cls.paiements
            if paiement.uuid_proposition == proposition_uuid and paiement.effectue
        )


PaiementFraisDossierInMemory.reset()
