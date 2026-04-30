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
from admission.ddd.admission.shared_kernel.domain.model.poste_diplomatique import PosteDiplomatiqueIdentity
from base.ddd.utils.business_validator import BusinessValidator
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceAcademiqueDTO
from osis_profile import BE_ISO_CODE, PLUS_5_ISO_CODES


@attr.dataclass(frozen=True, slots=True)
class ShouldVisaEtreComplete(BusinessValidator):
    pays_nationalite: str
    pays_nationalite_europeen: Optional[bool]
    pays_residence: str

    poste_diplomatique: Optional[PosteDiplomatiqueIdentity]

    candidat_est_inscrit_recemment_ucl: bool

    def validate(self, *args, **kwargs):
        if (
            self.pays_nationalite
            and self.pays_residence
            and self.pays_nationalite_europeen is False
            and self.pays_nationalite not in PLUS_5_ISO_CODES
            and self.pays_residence != BE_ISO_CODE
            and not self.poste_diplomatique
            and not self.candidat_est_inscrit_recemment_ucl
        ):
            raise InformationsVisaNonCompleteesException


@attr.dataclass(frozen=True, slots=True)
class ShouldInformationsBama15EtreCompletees(BusinessValidator):
    experiences_academiques: list[ExperienceAcademiqueDTO]
    est_potentiellement_concerne_par_le_bama_15: bool
    est_concerne_par_le_bama_15: bool | None
    preuve_bama_15: list[str]

    candidat_est_inscrit_recemment_ucl: bool

    def validate(self, *args, **kwargs):
        if (
            self.est_potentiellement_concerne_par_le_bama_15
            and not self.candidat_est_inscrit_recemment_ucl
            and (
                self.est_concerne_par_le_bama_15 is None or self.est_concerne_par_le_bama_15 and not self.preuve_bama_15
            )
        ):
            raise InformationsBama15NonCompleteesException
