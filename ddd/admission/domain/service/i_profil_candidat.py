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
from abc import abstractmethod
from typing import List, Dict

from admission.ddd.admission.doctorat.preparation.dtos.curriculum import CurriculumAdmissionDTO
from admission.ddd.admission.dtos.resume import ResumeCandidatDTO
from admission.ddd.admission.enums.valorisation_experience import ExperiencesCVRecuperees
from ddd.logic.shared_kernel.profil.dtos.etudes_secondaires import ValorisationEtudesSecondairesDTO
from osis_common.ddd import interface


class IProfilCandidatTranslator(interface.DomainService):
    NB_MAX_ANNEES_CV_REQUISES = 5
    MOIS_DEBUT_ANNEE_ACADEMIQUE_A_VALORISER = 9
    MOIS_FIN_ANNEE_ACADEMIQUE_A_VALORISER = 2

    @classmethod
    @abstractmethod
    def get_curriculum(
        cls,
        matricule: str,
        annee_courante: int,
        uuid_proposition: str,
        experiences_cv_recuperees: ExperiencesCVRecuperees = ExperiencesCVRecuperees.TOUTES,
    ) -> 'CurriculumAdmissionDTO':
        raise NotImplementedError

    @classmethod
    def get_date_maximale_curriculum(cls):
        """Retourne la date de la dernière expérience à remplir dans le CV (mois précédent la date du jour)."""
        return (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).replace(day=1)

    @classmethod
    def get_changements_etablissement(cls, matricule: str, annees: List[int]) -> Dict[int, bool]:
        """Inscrit à un autre établissement Belge en N-1
        (informatiquement : curriculum / en N-1 supérieur belge non-diplômé)"""
        raise NotImplementedError

    @classmethod
    def est_potentiel_vae(cls, matricule: str) -> bool:
        raise NotImplementedError

    @classmethod
    def valorisation_etudes_secondaires(cls, matricule: str) -> ValorisationEtudesSecondairesDTO:
        """Retourne les données de valorisation des études secondaires."""
        raise NotImplementedError

    @classmethod
    def recuperer_toutes_informations_candidat(
        cls,
        matricule: str,
        formation: str,
        annee_courante: int,
        uuid_proposition: str,
        experiences_cv_recuperees: ExperiencesCVRecuperees = ExperiencesCVRecuperees.TOUTES,
    ) -> ResumeCandidatDTO:
        """Retourne toutes les données relatives à un candidat nécessaires à son admission."""
        raise NotImplementedError
