# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from abc import abstractmethod
from typing import List, Optional

from admission.ddd.projet_doctoral.preparation.dtos import (
    ConditionsComptabiliteDTO,
    CoordonneesDTO,
    CurriculumDTO,
    IdentificationDTO,
)
from osis_common.ddd import interface


class IProfilCandidatTranslator(interface.DomainService):
    NB_MAX_ANNEES_CV_REQUISES = 5
    MOIS_DEBUT_ANNEE_ACADEMIQUE = 9
    MOIS_FIN_ANNEE_ACADEMIQUE = 6

    @classmethod
    @abstractmethod
    def get_identification(cls, matricule: str) -> 'IdentificationDTO':
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_coordonnees(cls, matricule: str) -> 'CoordonneesDTO':
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_langues_connues(cls, matricule: str) -> List[str]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_curriculum(cls, matricule: str, annee_courante: int) -> 'CurriculumDTO':
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_conditions_comptabilite(
        cls,
        matricule: str,
        annee_courante: int,
    ) -> 'ConditionsComptabiliteDTO':
        raise NotImplementedError

    @classmethod
    def get_annee_minimale_a_completer_cv(
        cls,
        annee_courante: int,
        annee_diplome_etudes_secondaires_belges: Optional[int] = None,
        annee_diplome_etudes_secondaires_etrangeres: Optional[int] = None,
        annee_derniere_inscription_ucl: Optional[int] = None,
    ):
        return 1 + max(
            [
                annee
                for annee in [
                    annee_courante - cls.NB_MAX_ANNEES_CV_REQUISES,
                    annee_diplome_etudes_secondaires_belges,
                    annee_diplome_etudes_secondaires_etrangeres,
                    annee_derniere_inscription_ucl,
                ]
                if annee
            ]
        )
