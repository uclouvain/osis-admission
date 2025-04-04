##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.domain.model.formation import (
    FORMATIONS_AVEC_BOURSES,
    est_formation_medecine_ou_dentisterie,
)
from admission.ddd.admission.dtos.campus import CampusDTO
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class FormationDTO(interface.DTO):
    sigle: str
    code: str
    annee: int
    date_debut: Optional[datetime.date]
    intitule: str
    intitule_fr: str
    intitule_en: str
    campus: Optional[CampusDTO]
    type: str
    code_domaine: str
    campus_inscription: Optional[CampusDTO]
    sigle_entite_gestion: str
    credits: Optional[int]

    def __str__(self):
        return f'{self.sigle} - {self.intitule or self.intitule_fr} ({self.campus})'

    @property
    def nom_complet(self):
        return f'{self.sigle} - {self.intitule or self.intitule_fr}'

    @property
    def est_formation_medecine_ou_dentisterie(self) -> bool:
        return est_formation_medecine_ou_dentisterie(self.code_domaine)

    @property
    def est_formation_avec_bourse(self) -> bool:
        return self.type in FORMATIONS_AVEC_BOURSES


@attr.dataclass(frozen=True, slots=True)
class BaseFormationDTO(interface.DTO):
    uuid: str
    sigle: str
    intitule: str
    lieu_enseignement: str
    annee: int

    def __str__(self):
        return f'{self.sigle} - {self.intitule} ({self.lieu_enseignement})'
