##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
from functools import reduce
from typing import List, Optional

import attr
from dateutil import relativedelta

from admission.ddd import NB_MOIS_MIN_VAE
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class AnneeExperienceAcademiqueDTO(interface.DTO):
    annee: int
    resultat: str
    releve_notes: List[str]
    traduction_releve_notes: List[str]
    credits_inscrits: Optional[float]
    credits_acquis: Optional[float]


@attr.dataclass(frozen=True, slots=True)
class ExperienceAcademiqueDTO(interface.DTO):
    uuid: str
    pays: str
    nom_pays: str
    nom_institut: str
    adresse_institut: str
    code_institut: str
    communaute_institut: str
    regime_linguistique: str
    nom_regime_linguistique: str
    type_releve_notes: str
    releve_notes: List[str]
    traduction_releve_notes: List[str]
    annees: List[AnneeExperienceAcademiqueDTO]
    a_obtenu_diplome: bool
    diplome: List[str]
    traduction_diplome: List[str]
    rang_diplome: str
    date_prevue_delivrance_diplome: Optional[datetime.date]
    titre_memoire: str
    note_memoire: str
    resume_memoire: List[str]
    grade_obtenu: str
    autre_grade_obtenu: str
    systeme_evaluation: str
    nom_formation: str
    type_enseignement: str

    def __str__(self):
        return self.nom_formation


@attr.dataclass(frozen=True, slots=True)
class ExperienceNonAcademiqueDTO(interface.DTO):
    uuid: str
    employeur: str
    date_debut: datetime.date
    date_fin: datetime.date
    type: str
    certificat: List[str]
    fonction: str
    secteur: str
    autre_activite: str


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
