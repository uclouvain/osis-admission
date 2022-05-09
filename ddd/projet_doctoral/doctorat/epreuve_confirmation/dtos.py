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
import datetime
from typing import Optional, List

import attr

from osis_common.ddd import interface


@attr.s(frozen=True, slots=True, auto_attribs=True)
class DemandeProlongationDTO(interface.DTO):
    nouvelle_echeance: datetime.date
    justification_succincte: str
    lettre_justification: List[str] = attr.Factory(list)
    avis_cdd: Optional[str] = ''


@attr.s(frozen=True, slots=True, auto_attribs=True)
class EpreuveConfirmationDTO(interface.DTO):
    uuid: str

    date_limite: datetime.date
    date: Optional[datetime.date] = None
    rapport_recherche: List[str] = attr.Factory(list)

    demande_prolongation: Optional[DemandeProlongationDTO] = None

    proces_verbal_ca: List[str] = attr.Factory(list)
    attestation_reussite: List[str] = attr.Factory(list)
    attestation_echec: List[str] = attr.Factory(list)
    demande_renouvellement_bourse: List[str] = attr.Factory(list)
    avis_renouvellement_mandat_recherche: List[str] = attr.Factory(list)
