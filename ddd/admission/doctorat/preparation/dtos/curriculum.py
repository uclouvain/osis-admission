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

from functools import reduce
from typing import List, Optional

import attr
from dateutil import relativedelta

from admission.ddd import NB_MOIS_MIN_VAE
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceAcademiqueDTO, ExperienceNonAcademiqueDTO
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class AnneeExperienceAcademiqueDTO(interface.DTO):
    uuid: str
    annee: int
    resultat: str
    releve_notes: List[str]
    traduction_releve_notes: List[str]
    credits_inscrits: Optional[float]
    credits_acquis: Optional[float]
    avec_bloc_1: Optional[bool]
    avec_complement: Optional[bool]
    credits_inscrits_communaute_fr: Optional[float]
    credits_acquis_communaute_fr: Optional[float]
    allegement: str
    est_reorientation_102: Optional[bool]


@attr.dataclass(frozen=True, slots=True)
class CurriculumDTO(interface.DTO):
    experiences_non_academiques: List[ExperienceNonAcademiqueDTO]
    experiences_academiques: List[ExperienceAcademiqueDTO]
    annee_derniere_inscription_ucl: Optional[int]
    annee_diplome_etudes_secondaires: Optional[int]
    annee_minimum_a_remplir: Optional[int]

    def _compte_nombre_mois(self, nb_total_mois, experience):
        delta = relativedelta.relativedelta(experience.date_fin, experience.date_debut)
        return nb_total_mois + (12 * delta.years + delta.months) + 1

    @property
    def candidat_est_potentiel_vae(self) -> bool:
        """
        Un candidat est potentiel vae si la durée de l'ensemble de ses expériences non academiques est supérieure à 36.
        """
        return (
            reduce(
                lambda total, experience: self._compte_nombre_mois(total, experience),
                self.experiences_non_academiques,
                0,
            )
            >= NB_MOIS_MIN_VAE
        )


@attr.dataclass(frozen=True, slots=True)
class CurriculumAExperiencesDTO(interface.DTO):
    a_experience_academique: bool
    a_experience_non_academique: bool
