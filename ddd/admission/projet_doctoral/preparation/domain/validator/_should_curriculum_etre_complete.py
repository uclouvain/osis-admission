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
import datetime
from typing import List, Optional, Tuple

import attr

from admission.ddd.admission.projet_doctoral.preparation.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.projet_doctoral.preparation.domain.validator.exceptions import (
    AnneesCurriculumNonSpecifieesException,
    FichierCurriculumNonRenseigneException,
)
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldAnneesCVRequisesCompletees(BusinessValidator):
    annee_courante: int
    annee_derniere_inscription_ucl: Optional[int]
    annee_diplome_etudes_secondaires_belges: Optional[int]
    annee_diplome_etudes_secondaires_etrangeres: Optional[int]
    dates_experiences_non_academiques: List[Tuple[datetime.date, datetime.date]]
    annees_experiences_academiques: List[int]

    def validate(self, *args, **kwargs):
        annee_minimale = 1 + max(
            [
                annee
                for annee in [
                    self.annee_courante - IProfilCandidatTranslator.NB_MAX_ANNEES_CV_REQUISES,
                    self.annee_diplome_etudes_secondaires_belges,
                    self.annee_diplome_etudes_secondaires_etrangeres,
                    self.annee_derniere_inscription_ucl,
                ]
                if annee
            ]
        )

        annees_valorisees = set(self.annees_experiences_academiques)

        # Vérifier si certaines années sont valorisées par les expériences non-académiques
        if self.dates_experiences_non_academiques:
            annees_restantes_a_valoriser = [
                [
                    datetime.date(a, IProfilCandidatTranslator.MOIS_DEBUT_ANNEE_ACADEMIQUE, 1),
                    datetime.date(a + 1, IProfilCandidatTranslator.MOIS_FIN_ANNEE_ACADEMIQUE, 1),
                ]
                for a in range(self.annee_courante, annee_minimale - 1, -1)
                if a not in annees_valorisees
            ]

            if annees_restantes_a_valoriser:

                iterateur_dates_experiences_non_academiques = iter(self.dates_experiences_non_academiques)
                periode_valorisee = list(next(iterateur_dates_experiences_non_academiques))

                for debut, fin in iterateur_dates_experiences_non_academiques:
                    if (periode_valorisee[0] - fin).days <= 1:
                        # Extension de la période de valorisation
                        periode_valorisee = (debut, max(fin, periode_valorisee[1]))
                    else:
                        # Rupture dans la période couverte par les expériences -> vérifier si elle valorise des années
                        annees_restantes_a_valoriser_tmp = []
                        for annee in annees_restantes_a_valoriser:
                            if annee[0] >= periode_valorisee[0] and annee[1] <= periode_valorisee[1]:
                                annees_valorisees.add(annee[0].year)
                            else:
                                annees_restantes_a_valoriser_tmp.append(annee)

                        # On passe à la période suivante avec les années restantes
                        periode_valorisee = [debut, fin]
                        annees_restantes_a_valoriser = annees_restantes_a_valoriser_tmp

                        if not annees_restantes_a_valoriser:
                            break

                # Vérifier la valorisation des années pour la dernière période
                for annee in annees_restantes_a_valoriser:
                    if annee[0] >= periode_valorisee[0] and annee[1] <= periode_valorisee[1]:
                        annees_valorisees.add(annee[0].year)

        annees_manquantes = [
            f'{annee}-{annee+1}'
            for annee in range(self.annee_courante, annee_minimale - 1, -1)
            if annee not in annees_valorisees
        ]

        if annees_manquantes:
            raise AnneesCurriculumNonSpecifieesException(annees_manquantes=annees_manquantes)


@attr.dataclass(frozen=True, slots=True)
class ShouldCurriculumFichierEtreSpecifie(BusinessValidator):
    fichier_pdf: List[str]

    def validate(self, *args, **kwargs):
        if not self.fichier_pdf:
            raise FichierCurriculumNonRenseigneException
