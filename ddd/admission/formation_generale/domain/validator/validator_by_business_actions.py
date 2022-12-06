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
from typing import List, Optional, Tuple

import attr

from admission.ddd.admission.doctorat.preparation.dtos.curriculum import ExperienceAcademiqueDTO
from admission.ddd.admission.domain.validator import ShouldAnneesCVRequisesCompletees
from admission.ddd.admission.formation_generale.domain.validator import (
    ShouldCurriculumFichierEtreSpecifie,
    ShouldEquivalenceEtreSpecifiee,
    ShouldContinuationCycleBachelierEtreSpecifiee,
    ShouldAttestationContinuationCycleBachelierEtreSpecifiee,
)
from base.ddd.utils.business_validator import BusinessValidator, TwoStepsMultipleBusinessExceptionListValidator
from base.models.enums.education_group_types import TrainingType


@attr.dataclass(frozen=True, slots=True)
class FormationGeneraleCurriculumValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    fichier_pdf: List[str]
    annee_courante: int
    annee_derniere_inscription_ucl: Optional[int]
    annee_diplome_etudes_secondaires_belges: Optional[int]
    annee_diplome_etudes_secondaires_etrangeres: Optional[int]
    dates_experiences_non_academiques: List[Tuple[datetime.date, datetime.date]]
    experiences_academiques: List[ExperienceAcademiqueDTO]
    type_formation: TrainingType
    continuation_cycle_bachelier: Optional[bool]
    attestation_continuation_cycle_bachelier: List[str]
    equivalence_diplome: List[str]
    sigle_formation: str

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldCurriculumFichierEtreSpecifie(
                fichier_pdf=self.fichier_pdf,
                type_formation=self.type_formation,
            ),
            ShouldAnneesCVRequisesCompletees(
                annee_courante=self.annee_courante,
                experiences_academiques=self.experiences_academiques,
                annee_derniere_inscription_ucl=self.annee_derniere_inscription_ucl,
                annee_diplome_etudes_secondaires_belges=self.annee_diplome_etudes_secondaires_belges,
                annee_diplome_etudes_secondaires_etrangeres=self.annee_diplome_etudes_secondaires_etrangeres,
                dates_experiences_non_academiques=self.dates_experiences_non_academiques,
            ),
            ShouldEquivalenceEtreSpecifiee(
                equivalence=self.equivalence_diplome,
                type_formation=self.type_formation,
                experiences_academiques=self.experiences_academiques,
            ),
            ShouldContinuationCycleBachelierEtreSpecifiee(
                continuation_cycle_bachelier=self.continuation_cycle_bachelier,
                type_formation=self.type_formation,
                experiences_academiques=self.experiences_academiques,
            ),
            ShouldAttestationContinuationCycleBachelierEtreSpecifiee(
                continuation_cycle_bachelier=self.continuation_cycle_bachelier,
                attestation_continuation_cycle_bachelier=self.attestation_continuation_cycle_bachelier,
                sigle_formation=self.sigle_formation,
            ),
        ]
