##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from __future__ import annotations

from typing import List
from typing import TYPE_CHECKING

import attr

from admission.ddd.projet_doctoral.validation.domain.validator._should_demande_status_a_verifier import (
    ShouldStatutDemandeAVerifier,
)
from base.ddd.utils.business_validator import TwoStepsMultipleBusinessExceptionListValidator, BusinessValidator

if TYPE_CHECKING:
    from admission.ddd.projet_doctoral.validation.domain.model.demande import Demande


@attr.s(frozen=True, slots=True, auto_attribs=True)
class RefuserDemandeCDDValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    demande: Demande

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldStatutDemandeAVerifier(demande=self.demande),
        ]


@attr.s(frozen=True, slots=True, auto_attribs=True)
class ApprouverDemandeCDDValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    demande: Demande

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldStatutDemandeAVerifier(demande=self.demande),
        ]
