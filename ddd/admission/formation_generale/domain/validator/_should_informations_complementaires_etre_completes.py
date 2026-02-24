# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional

import attr

from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    InformationsBama15NonCompleteesException,
    InformationsVisaNonCompleteesException,
)
from admission.ddd.admission.shared_kernel.domain.model.formation import Formation
from admission.ddd.admission.shared_kernel.domain.model.poste_diplomatique import PosteDiplomatiqueIdentity
from base.ddd.utils.business_validator import BusinessValidator
from base.models.enums.community import CommunityEnum
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceAcademiqueDTO
from osis_profile import BE_ISO_CODE, PLUS_5_ISO_CODES
from reference.models.enums.cycle import Cycle


@attr.dataclass(frozen=True, slots=True)
class ShouldVisaEtreComplete(BusinessValidator):
    pays_nationalite: str
    pays_nationalite_europeen: Optional[bool]
    pays_residence: str

    poste_diplomatique: Optional[PosteDiplomatiqueIdentity]

    def validate(self, *args, **kwargs):
        if (
            self.pays_nationalite
            and self.pays_residence
            and self.pays_nationalite_europeen is False
            and self.pays_nationalite not in PLUS_5_ISO_CODES
            and self.pays_residence != BE_ISO_CODE
            and not self.poste_diplomatique
        ):
            raise InformationsVisaNonCompleteesException


@attr.dataclass(frozen=True, slots=True)
class ShouldInformationsBama15EtreCompletees(BusinessValidator):
    experiences_academiques: list[ExperienceAcademiqueDTO]
    formation: Formation
    annee_formation: int
    est_concerne_par_le_bama_15: bool | None
    preuve_bama_15: list[str]

    def validate(self, *args, **kwargs):
        # Le candidat...
        if (
            # souhaite s'inscrire à une formation précise
            self.formation.est_formation_pour_bama_15
            # termine une formation de premier cycle FWB
            and any(
                experience.cycle_formation == Cycle.FIRST_CYCLE.name
                and experience.communaute_institut == CommunityEnum.FRENCH_SPEAKING.name
                and not experience.a_obtenu_diplome
                and not experience.est_autre_formation
                and any(annee.annee == self.annee_formation for annee in experience.annees)
                for experience in self.experiences_academiques
            )
            # n'a pas répondu aux questions relatives au bama 15
            and (
                self.est_concerne_par_le_bama_15 is None or self.est_concerne_par_le_bama_15 and not self.preuve_bama_15
            )
        ):
            raise InformationsBama15NonCompleteesException
