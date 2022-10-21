##############################################################################
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
##############################################################################
import datetime
from typing import Optional

import attr

from admission.ddd.admission.domain.model.bourse import (
    BourseDoubleDiplomeIdentity,
    BourseInternationaleIdentity,
    BourseErasmusMundusIdentity,
)
from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutProposition
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class PropositionIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True, hash=False, eq=False)
class Proposition(interface.RootEntity):
    entity_id: 'PropositionIdentity'
    formation_id: 'FormationIdentity'
    matricule_candidat: str
    statut: ChoixStatutProposition = ChoixStatutProposition.IN_PROGRESS

    creee_le: Optional[datetime.datetime] = None
    modifiee_le: Optional[datetime.datetime] = None

    bourse_double_diplome_id: Optional[BourseDoubleDiplomeIdentity] = None
    bourse_internationale_id: Optional[BourseInternationaleIdentity] = None
    bourse_erasmus_mundus_id: Optional[BourseErasmusMundusIdentity] = None
