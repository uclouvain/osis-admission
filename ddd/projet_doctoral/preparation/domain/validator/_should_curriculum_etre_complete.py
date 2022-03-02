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
from typing import List, Optional, Set

import attr

from admission.ddd.projet_doctoral.preparation.domain.validator.exceptions import (
    AnneesCurriculumNonSpecifieesException,
    FichierCurriculumNonRenseigneException,
)
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldAnneesCVRequisesCompletees(BusinessValidator):
    annees: Set[int]
    nb_maximum_annees_requises: int
    annee_courante: int
    annee_derniere_inscription_ucl: Optional[int]
    annee_diplome_etudes_secondaires_belges: Optional[int]
    annee_diplome_etudes_secondaires_etrangeres: Optional[int]

    def validate(self, *args, **kwargs):
        annee_minimale = max(
            [
                annee
                for annee in [
                    self.annee_courante - self.nb_maximum_annees_requises,
                    self.annee_diplome_etudes_secondaires_belges,
                    self.annee_diplome_etudes_secondaires_etrangeres,
                    self.annee_derniere_inscription_ucl,
                ]
                if annee
            ]
        )

        annees_manquantes = [
            str(annee) for annee in range(self.annee_courante, annee_minimale, -1) if annee not in self.annees
        ]

        if annees_manquantes:
            raise AnneesCurriculumNonSpecifieesException(annees_manquantes=annees_manquantes)


@attr.dataclass(frozen=True, slots=True)
class ShouldCurriculumFichierEtreSpecifie(BusinessValidator):
    fichier_pdf: List[str]

    def validate(self, *args, **kwargs):
        if not self.fichier_pdf:
            raise FichierCurriculumNonRenseigneException
