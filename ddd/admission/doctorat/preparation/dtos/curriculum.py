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
from typing import List, Optional, Tuple

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class AnneeExperienceAcademiqueDTO(interface.DTO):
    annee: int
    resultat: str


@attr.dataclass(frozen=True, slots=True)
class ExperienceAcademiqueDTO(interface.DTO):
    pays: str
    annees: List[AnneeExperienceAcademiqueDTO]


@attr.dataclass(frozen=True, slots=True)
class CurriculumDTO(interface.DTO):
    dates_experiences_non_academiques: List[Tuple[datetime.date, datetime.date]]
    experiences_academiques: List[ExperienceAcademiqueDTO]
    annee_derniere_inscription_ucl: Optional[int]
    annee_diplome_etudes_secondaires_belges: Optional[int]
    annee_diplome_etudes_secondaires_etrangeres: Optional[int]
