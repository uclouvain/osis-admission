# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from typing import List, Optional

import attr

from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixInscriptionATitre,
    ChoixMoyensDecouverteFormation,
)
from admission.ddd.admission.formation_continue.domain.validator import (
    ShouldRenseignerInformationsAdditionnelles,
    ShouldRenseignerChoixDeFormation,
    ShouldFormationEtreOuverte,
)
from base.ddd.utils.business_validator import BusinessValidator, TwoStepsMultipleBusinessExceptionListValidator
from ddd.logic.formation_catalogue.formation_continue.dtos.informations_specifiques import InformationsSpecifiquesDTO


@attr.dataclass(frozen=True, slots=True)
class InformationsComplementairesValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    inscription_a_titre: Optional[ChoixInscriptionATitre] = None

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldRenseignerInformationsAdditionnelles(
                inscription_a_titre=self.inscription_a_titre,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class ChoixFormationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    motivations: str
    moyens_decouverte_formation: List[ChoixMoyensDecouverteFormation]
    informations_specifiques_formation: Optional[InformationsSpecifiquesDTO]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldRenseignerChoixDeFormation(
                motivations=self.motivations,
                moyens_decouverte_formation=self.moyens_decouverte_formation,
                informations_specifiques_formation=self.informations_specifiques_formation,
            ),
            ShouldFormationEtreOuverte(
                informations_specifiques_formation=self.informations_specifiques_formation,
            ),
        ]
