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
from typing import Dict, List, Optional

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True, auto_attribs=True)
class RechercherFormationGeneraleQuery(interface.QueryRequest):
    type_formation: str
    intitule_formation: str
    campus: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class InitierPropositionCommand(interface.CommandRequest):
    sigle_formation: str
    annee_formation: int
    matricule_candidat: str

    bourse_double_diplome: Optional[str] = ''
    bourse_internationale: Optional[str] = ''
    bourse_erasmus_mundus: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class ListerPropositionsCandidatQuery(interface.QueryRequest):
    matricule_candidat: str


@attr.dataclass(frozen=True, slots=True)
class RecupererPropositionQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class ModifierChoixFormationCommand(interface.CommandRequest):
    uuid_proposition: str

    sigle_formation: str
    annee_formation: int

    bourse_double_diplome: Optional[str] = ''
    bourse_internationale: Optional[str] = ''
    bourse_erasmus_mundus: Optional[str] = ''

    reponses_questions_specifiques: Dict = attr.Factory(dict)


@attr.dataclass(frozen=True, slots=True)
class SupprimerPropositionCommand(interface.CommandRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class VerifierPropositionQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class SoumettrePropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    annee: int
    pool: str


@attr.dataclass(frozen=True, slots=True)
class CompleterCurriculumCommand(interface.CommandRequest):
    uuid_proposition: str

    continuation_cycle_bachelier: Optional[bool] = None
    attestation_continuation_cycle_bachelier: List[str] = attr.Factory(list)
    curriculum: List[str] = attr.Factory(list)
    equivalence_diplome: List[str] = attr.Factory(list)
    reponses_questions_specifiques: Dict = attr.Factory(dict)


@attr.dataclass(frozen=True, slots=True)
class VerifierCurriculumQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class DeterminerAnneeAcademiqueEtPotQuery(interface.QueryRequest):
    uuid_proposition: str
