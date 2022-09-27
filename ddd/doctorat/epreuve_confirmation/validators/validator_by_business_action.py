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

from admission.ddd.doctorat.epreuve_confirmation.domain.model._demande_prolongation import (
    DemandeProlongation,
)
from admission.ddd.doctorat.epreuve_confirmation.validators import (
    ShouldEpreuveConfirmationEtreCompletee,
    ShouldDateEpreuveEtreValide,
    ShouldDemandeProlongationEtreCompletee,
    ShouldAvisProlongationEtreComplete,
    ShouldDemandeProlongationEtreDefinie,
    ShouldDemandeProlongationEtreCompleteePourEvaluation,
)
from base.ddd.utils.business_validator import TwoStepsMultipleBusinessExceptionListValidator, BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class SoumettreEpreuveConfirmationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    date: Optional[datetime.date]
    date_limite: datetime.date

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldEpreuveConfirmationEtreCompletee(self.date),
            ShouldDateEpreuveEtreValide(self.date, self.date_limite),
        ]


@attr.dataclass(frozen=True, slots=True)
class SoumettreDemandeProlongationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    nouvelle_echeance: datetime.date
    justification_succincte: str

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldDemandeProlongationEtreCompletee(
                self.nouvelle_echeance,
                self.justification_succincte,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class SoumettreAvisProlongationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    nouvel_avis_cdd: str
    demande_prolongation: Optional[DemandeProlongation]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldDemandeProlongationEtreDefinie(self.demande_prolongation),
            ShouldAvisProlongationEtreComplete(self.nouvel_avis_cdd),
        ]


@attr.dataclass(frozen=True, slots=True)
class EncodageDecisionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    date: Optional[datetime.date]
    proces_verbal_ca: List[str]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldDemandeProlongationEtreCompleteePourEvaluation(
                date=self.date,
                proces_verbal_ca=self.proces_verbal_ca,
            ),
        ]
