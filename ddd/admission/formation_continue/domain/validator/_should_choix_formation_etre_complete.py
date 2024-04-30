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
from typing import Optional, List

import attr

from admission.ddd.admission.formation_continue.domain.model.enums import ChoixMoyensDecouverteFormation
from admission.ddd.admission.formation_continue.domain.validator.exceptions import (
    ChoixDeFormationNonRenseigneException,
    FormationEstFermeeException,
)
from base.ddd.utils.business_validator import BusinessValidator
from base.models.enums.state_iufc import StateIUFC
from ddd.logic.formation_catalogue.formation_continue.dtos.informations_specifiques import InformationsSpecifiquesDTO


@attr.dataclass(frozen=True, slots=True)
class ShouldRenseignerChoixDeFormation(BusinessValidator):
    motivations: str
    moyens_decouverte_formation: List[ChoixMoyensDecouverteFormation]
    informations_specifiques_formation: Optional[InformationsSpecifiquesDTO]

    def validate(self, *args, **kwargs):
        if not self.motivations or (
            self.informations_specifiques_formation
            and self.informations_specifiques_formation.inscription_au_role_obligatoire is True
            and not self.moyens_decouverte_formation
        ):
            raise ChoixDeFormationNonRenseigneException


@attr.dataclass(frozen=True, slots=True)
class ShouldFormationEtreOuverte(BusinessValidator):
    informations_specifiques_formation: Optional[InformationsSpecifiquesDTO]

    def validate(self, *args, **kwargs):
        if self.informations_specifiques_formation and self.informations_specifiques_formation.etat == StateIUFC.CLOSED:
            raise FormationEstFermeeException(self.informations_specifiques_formation.sigle_formation)
