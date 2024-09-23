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
from typing import List

import attr

from admission.ddd.admission.formation_continue.domain.model.statut_checklist import StatutChecklist
from admission.ddd.admission.formation_continue.domain.validator import (
    ShouldRenseignerExperiencesCurriculum,
)
from admission.ddd.admission.formation_continue.domain.validator._should_informations_checklist_etre_completees import (
    ShouldPeutMettreEnAttente,
    ShouldPeutApprouverParFac,
    ShouldPeutRefuserProposition,
    ShouldPeutAnnulerProposition,
    ShouldPeutApprouverProposition,
    ShouldPeutCloturerProposition,
    ShouldPeutMettreAValider,
)
from base.ddd.utils.business_validator import BusinessValidator, TwoStepsMultipleBusinessExceptionListValidator


@attr.dataclass(frozen=True, slots=True)
class FormationContinueCurriculumValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    a_experience_academique: bool
    a_experience_non_academique: bool

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldRenseignerExperiencesCurriculum(
                a_experience_academique=self.a_experience_academique,
                a_experience_non_academique=self.a_experience_non_academique,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class MettreEnAttenteValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    checklist_statut: StatutChecklist

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPeutMettreEnAttente(
                checklist_statut=self.checklist_statut,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class ApprouverParFacValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    checklist_statut: StatutChecklist

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPeutApprouverParFac(
                checklist_statut=self.checklist_statut,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class RefuserPropositionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    checklist_statut: StatutChecklist

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPeutRefuserProposition(
                checklist_statut=self.checklist_statut,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class AnnulerPropositionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    checklist_statut: StatutChecklist

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPeutAnnulerProposition(
                checklist_statut=self.checklist_statut,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class ApprouverPropositionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    checklist_statut: StatutChecklist

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPeutApprouverProposition(
                checklist_statut=self.checklist_statut,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class MettreAValiderValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    checklist_statut: StatutChecklist

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPeutMettreAValider(
                checklist_statut=self.checklist_statut,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class CloturerPropositionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    checklist_statut: StatutChecklist

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPeutCloturerProposition(
                checklist_statut=self.checklist_statut,
            ),
        ]
