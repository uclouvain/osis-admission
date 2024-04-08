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
from typing import List

import attr

from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    FichierCurriculumNonRenseigneException,
    EquivalenceNonRenseigneeException,
)
from base.ddd.utils.business_validator import BusinessValidator
from base.models.enums.education_group_types import TrainingType
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceAcademiqueDTO
from osis_profile import BE_ISO_CODE


@attr.dataclass(frozen=True, slots=True)
class ShouldCurriculumFichierEtreSpecifie(BusinessValidator):
    fichier_pdf: List[str]
    type_formation: TrainingType

    def validate(self, *args, **kwargs):
        if self.type_formation != TrainingType.BACHELOR and not self.fichier_pdf:
            raise FichierCurriculumNonRenseigneException


@attr.dataclass(frozen=True, slots=True)
class ShouldEquivalenceEtreSpecifiee(BusinessValidator):
    equivalence: List[str]
    type_formation: TrainingType
    experiences_academiques: List[ExperienceAcademiqueDTO]

    def validate(self, *args, **kwargs):
        experiences_avec_diplome = [
            experience for experience in self.experiences_academiques if experience.a_obtenu_diplome
        ]
        if (
            self.type_formation in [TrainingType.AGGREGATION, TrainingType.CAPAES]
            and not self.equivalence
            and experiences_avec_diplome
            and all(experience.pays != BE_ISO_CODE for experience in experiences_avec_diplome)
        ):
            raise EquivalenceNonRenseigneeException
