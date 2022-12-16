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
from typing import Dict, List, Optional, Union

import attr

from admission.ddd.admission.dtos.formation import FormationDTO
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class PropositionDTO(interface.DTO):
    uuid: str
    formation: FormationDTO
    annee_calculee: Optional[int]
    pot_calcule: Optional[str]
    date_fin_pot: Optional[datetime.date]
    creee_le: datetime.datetime
    modifiee_le: datetime.datetime
    erreurs: List[Dict[str, str]]
    statut: str

    matricule_candidat: str
    prenom_candidat: str
    nom_candidat: str

    reponses_questions_specifiques: Dict[str, Union[str, List[str]]]

    curriculum: List[str]
    equivalence_diplome: List[str]
