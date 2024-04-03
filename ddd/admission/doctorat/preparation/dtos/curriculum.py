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

import datetime
from functools import reduce
from typing import List, Optional

import attr
from dateutil import relativedelta
from django.template.defaultfilters import truncatechars
from django.utils.functional import cached_property

from admission.ddd import NB_MOIS_MIN_VAE, MOIS_DEBUT_ANNEE_ACADEMIQUE
from base.models.enums.community import CommunityEnum
from osis_common.ddd import interface
from osis_profile.models.enums.curriculum import ActivityType
from reference.models.enums.cycle import Cycle


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
class ExperienceAcademiqueDTO(interface.DTO):
    uuid: str
    pays: str
    nom_pays: str
    nom_institut: str
    adresse_institut: str
    code_institut: str
    communaute_institut: str
    type_institut: str
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
    systeme_evaluation: str
    nom_formation: str
    nom_formation_equivalente_communaute_fr: str
    est_autre_formation: Optional[bool]
    cycle_formation: str
    type_enseignement: str
    valorisee_par_admissions: Optional[List[str]] = None

    def __str__(self):
        return self.nom_formation

    @cached_property
    def est_formation_bachelier_fwb(self):
        return (
            self.cycle_formation == Cycle.FIRST_CYCLE.name
            and self.communaute_institut == CommunityEnum.FRENCH_SPEAKING.name
            and not self.a_obtenu_diplome
        )

    @cached_property
    def est_formation_master_fwb(self):
        return (
            self.cycle_formation == Cycle.SECOND_CYCLE.name
            and self.communaute_institut == CommunityEnum.FRENCH_SPEAKING.name
            and not self.a_obtenu_diplome
        )

    @cached_property
    def derniere_annee(self):
        return max(self.annees, key=lambda annee: annee.annee).annee

    @property
    def titre_formate(self):
        annee_minimale = min(self.annees, key=lambda annee: annee.annee)

        return "{annee_minimale}-{annee_maximale} : {nom_formation}".format(
            annee_minimale=annee_minimale.annee,
            annee_maximale=self.derniere_annee + 1,
            nom_formation=self.nom_formation_equivalente_communaute_fr or self.nom_formation,
        )

    @property
    def titre_pdf_decision_sic(self):
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
    valorisee_par_admissions: Optional[List[str]] = None

    def __str__(self):
        if self.type == ActivityType.OTHER.name:
            return self.autre_activite
        return str(ActivityType.get_value(self.type))

    @property
    def dates_formatees(self):
        date_debut = self.date_debut.strftime('%m/%Y')
        date_fin = self.date_fin.strftime('%m/%Y')
        return f"{date_debut}-{date_fin}" if date_debut != date_fin else date_debut

    @property
    def titre_formate(self):
        return f"{self.dates_formatees} : {self}"

    @cached_property
    def derniere_annee(self):
        return self.date_fin.year if self.date_fin.month >= MOIS_DEBUT_ANNEE_ACADEMIQUE else self.date_fin.year - 1

    @property
    def titre_pdf_decision_sic(self):
        return (
            f'{self.autre_activite} {self.dates_formatees}'
            if self.type == ActivityType.OTHER.name
            else self.dates_formatees
        )


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
