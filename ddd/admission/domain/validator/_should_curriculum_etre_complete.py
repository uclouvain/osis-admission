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
import datetime
from typing import List, Optional, Set, Dict

import attr
from dateutil.rrule import rrule, MONTHLY, rruleset

from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AnneesCurriculumNonSpecifieesException,
    ExperiencesAcademiquesNonCompleteesException,
)
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from base.ddd.utils.business_validator import BusinessValidator, MultipleBusinessExceptions
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceAcademiqueDTO, ExperienceNonAcademiqueDTO
from ddd.logic.shared_kernel.profil.dtos.parcours_interne import ExperienceParcoursInterneDTO


@attr.dataclass(frozen=True, slots=True)
class ShouldAnneesCVRequisesCompletees(BusinessValidator):
    annee_courante: int
    annee_derniere_inscription_ucl: Optional[int]
    annee_diplome_etudes_secondaires: Optional[int]
    experiences_non_academiques: List[ExperienceNonAcademiqueDTO]
    experiences_academiques: List[ExperienceAcademiqueDTO]
    experiences_academiques_incompletes: Dict[str, str]
    experiences_parcours_interne: Optional[List[ExperienceParcoursInterneDTO]] = None
    date_soumission: Optional[datetime.date] = None
    date_debut_formation: Optional[datetime.date] = None

    def validate(self, *args, **kwargs):
        annee_minimale = IProfilCandidatTranslator.get_annee_minimale_a_completer_cv(
            annee_courante=self.annee_courante,
            annee_diplome_etudes_secondaires=self.annee_diplome_etudes_secondaires,
            annee_derniere_inscription_ucl=self.annee_derniere_inscription_ucl,
        )

        # Les expériences académiques externes complètes valorisent certaines années
        annees_valorisees = set(
            [
                annee.annee
                for xp in self.experiences_academiques
                if xp.uuid not in self.experiences_academiques_incompletes
                for annee in xp.annees
            ]
        )

        # Les expériences académiques internes valides valorisent certaines années
        if self.experiences_parcours_interne:
            for experience_interne in self.experiences_parcours_interne:
                for annee_experience_interne in experience_interne.annees:
                    if not annee_experience_interne.etat_inscription_en_erreur:
                        annees_valorisees.add(annee_experience_interne.annee)

        dernier_mois_a_valoriser = IProfilCandidatTranslator.get_date_maximale_curriculum(
            date_soumission=self.date_soumission,
            date_debut_formation=self.date_debut_formation,
        )

        mois_a_valoriser = self._recuperer_tous_les_mois_restant_a_valoriser(
            annee_minimale=annee_minimale,
            dernier_mois_a_valoriser=dernier_mois_a_valoriser,
            annees_deja_valorisees=annees_valorisees,
        )

        nb_mois_a_valoriser = mois_a_valoriser.count()

        # Les activités non-académiques externes valorisent certains mois
        if self.experiences_non_academiques and mois_a_valoriser:
            nb_mois_a_valoriser = self.verifier_mois_valorises_par_les_experiences_non_academiques(
                mois_a_valoriser=mois_a_valoriser,
                nb_mois_a_valoriser=nb_mois_a_valoriser,
            )

        if nb_mois_a_valoriser > 0:
            exceptions = self._recuperer_exceptions_a_declencher_par_periode(mois_a_valoriser)

            raise MultipleBusinessExceptions(exceptions=exceptions)

    def verifier_mois_valorises_par_les_experiences_non_academiques(
        self,
        mois_a_valoriser: rruleset,
        nb_mois_a_valoriser: int,
    ):
        """Vérifier si certains mois sont valorisés par les expériences non-académiques."""
        iterateur_experiences_non_academiques = iter(self.experiences_non_academiques)
        experience = next(iterateur_experiences_non_academiques)
        periode_valorisee = [experience.date_debut, experience.date_fin]

        for experience in iterateur_experiences_non_academiques:
            if (periode_valorisee[0] - experience.date_fin).days <= 1:
                # Extension de la période de valorisation
                periode_valorisee = [experience.date_debut, max(experience.date_fin, periode_valorisee[1])]
            else:
                # Rupture dans la période couverte par les expériences -> vérifier si elle valorise des mois
                for mois in iter(mois_a_valoriser):
                    if periode_valorisee[0] <= mois.date() <= periode_valorisee[1]:
                        mois_a_valoriser.exdate(mois)
                        nb_mois_a_valoriser -= 1
                    elif mois.date() > periode_valorisee[1]:
                        break

                # On passe à la période suivante
                periode_valorisee = [experience.date_debut, experience.date_fin]

                if nb_mois_a_valoriser == 0:
                    break

        # Vérifier la valorisation des années pour la dernière période
        for mois in iter(mois_a_valoriser):
            if periode_valorisee[0] <= mois.date() <= periode_valorisee[1]:
                mois_a_valoriser.exdate(mois)
                nb_mois_a_valoriser -= 1
            elif mois.date() > periode_valorisee[1]:
                break

        return nb_mois_a_valoriser

    def _recuperer_exceptions_a_declencher_par_periode(
        self,
        mois_a_valoriser: rruleset,
    ) -> Set[AnneesCurriculumNonSpecifieesException]:
        """Retourne un ensemble d'exceptions constituée d'une exception par suite de mois consécutifs non valorisés."""
        exceptions = set()
        periode_courante = [mois_a_valoriser[0], mois_a_valoriser[0]]
        intervalle_mois = datetime.timedelta(days=31)
        for mois in iter(mois_a_valoriser):
            if (mois - periode_courante[1]) <= intervalle_mois:
                periode_courante[1] = mois
            else:
                exceptions.add(AnneesCurriculumNonSpecifieesException(periode_manquante=list(periode_courante)))
                periode_courante = [mois, mois]
        exceptions.add(AnneesCurriculumNonSpecifieesException(periode_manquante=periode_courante))
        return exceptions

    def _recuperer_tous_les_mois_restant_a_valoriser(
        self,
        annee_minimale: int,
        dernier_mois_a_valoriser: datetime.date,
        annees_deja_valorisees: Set[int],
    ) -> rruleset:
        """Renvoie la suite des mois qui restent à valoriser après prise en compte des expériences académiques."""
        mois_a_valoriser = rruleset()
        for annee in range(annee_minimale, self.annee_courante + 1):
            if annee not in annees_deja_valorisees:
                mois_a_valoriser.rrule(
                    rrule(
                        freq=MONTHLY,
                        dtstart=datetime.date(
                            annee,
                            IProfilCandidatTranslator.MOIS_DEBUT_ANNEE_ACADEMIQUE_A_VALORISER,
                            1,
                        ),
                        until=min(
                            dernier_mois_a_valoriser,
                            datetime.date(
                                annee + 1,
                                IProfilCandidatTranslator.MOIS_FIN_ANNEE_ACADEMIQUE_A_VALORISER,
                                1,
                            ),
                        ),
                    )
                )
        return mois_a_valoriser


@attr.dataclass(frozen=True, slots=True)
class ShouldExperiencesAcademiquesEtreCompletees(BusinessValidator):
    experiences_academiques_incompletes: Dict[str, str]

    def validate(self, *args, **kwargs):
        if self.experiences_academiques_incompletes:
            raise MultipleBusinessExceptions(
                exceptions=set(
                    ExperiencesAcademiquesNonCompleteesException(
                        reference=experience_uuid,
                        name=experience_name,
                    )
                    for experience_uuid, experience_name in self.experiences_academiques_incompletes.items()
                )
            )
