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
    releve_notes: List[str]
    traduction_releve_notes: List[str]


@attr.dataclass(frozen=True, slots=True)
class ExperienceAcademiqueDTO(interface.DTO):
    uuid: str
    pays: str
    regime_linguistique: str
    type_releve_notes: str
    releve_notes: List[str]
    traduction_releve_notes: List[str]
    annees: List[AnneeExperienceAcademiqueDTO]
    a_obtenu_diplome: bool
    diplome: List[str]
    traduction_diplome: List[str]
    rang_diplome: str
    date_prevue_delivrance_diplome: Optional[datetime.date]
    titre_memoire: str
    note_memoire: str
    resume_memoire: List[str]


@attr.dataclass(frozen=True, slots=True)
class CurriculumDTO(interface.DTO):
    dates_experiences_non_academiques: List[Tuple[datetime.date, datetime.date]]
    experiences_academiques: List[ExperienceAcademiqueDTO]
    annee_derniere_inscription_ucl: Optional[int]
    annee_diplome_etudes_secondaires_belges: Optional[int]
    annee_diplome_etudes_secondaires_etrangeres: Optional[int]
