# ##############################################################################
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
# ##############################################################################
import datetime
from abc import abstractmethod
from typing import Dict, List, Optional

from admission.ddd.admission.doctorat.preparation.dtos import (
    ConditionsComptabiliteDTO,
    CurriculumDTO,
)
from admission.ddd.admission.doctorat.preparation.dtos.comptabilite import (
    DerniersEtablissementsSuperieursCommunauteFrancaiseFrequentesDTO,
)
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import CurriculumAExperiencesDTO
from admission.ddd.admission.dtos import CoordonneesDTO, EtudesSecondairesAdmissionDTO, IdentificationDTO
from admission.ddd.admission.dtos.resume import ResumeCandidatDTO
from admission.ddd.admission.enums.valorisation_experience import ExperiencesCVRecuperees
from base.models.enums.community import CommunityEnum
from base.tasks.synchronize_entities_addresses import UCLouvain_acronym
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceAcademiqueDTO
from osis_common.ddd import interface


class IProfilCandidatTranslator(interface.DomainService):
    NB_MAX_ANNEES_CV_REQUISES = 5
    MOIS_DEBUT_ANNEE_ACADEMIQUE_A_VALORISER = 9
    MOIS_FIN_ANNEE_ACADEMIQUE_A_VALORISER = 2

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
    def get_etudes_secondaires(cls, matricule: str) -> 'EtudesSecondairesAdmissionDTO':
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_curriculum(cls, matricule: str, annee_courante: int, uuid_proposition: str) -> 'CurriculumDTO':
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_existence_experiences_curriculum(cls, matricule: str) -> 'CurriculumAExperiencesDTO':
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
        annee_diplome_etudes_secondaires: Optional[int] = None,
        annee_derniere_inscription_ucl: Optional[int] = None,
    ):
        return 1 + max(
            [
                annee
                for annee in [
                    annee_courante - cls.NB_MAX_ANNEES_CV_REQUISES,
                    annee_diplome_etudes_secondaires,
                    annee_derniere_inscription_ucl,
                ]
                if annee
            ]
        )

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
    def etudes_secondaires_valorisees(cls, matricule: str) -> bool:
        """Spécifie si les études secondaires ont été valorisées."""
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

    @classmethod
    def recuperer_derniers_etablissements_superieurs_communaute_fr_frequentes(
        cls,
        experiences_academiques: List[ExperienceAcademiqueDTO],
        annee_minimale: int,
    ) -> Optional[DerniersEtablissementsSuperieursCommunauteFrancaiseFrequentesDTO]:
        derniere_annee = 0
        noms = []

        for experience in experiences_academiques:
            derniere_annee_actuelle = max(experience_year.annee for experience_year in experience.annees)
            if (
                experience.communaute_institut == CommunityEnum.FRENCH_SPEAKING.name
                and experience.code_institut != UCLouvain_acronym
                and derniere_annee_actuelle >= annee_minimale
                and derniere_annee_actuelle >= derniere_annee
            ):
                if derniere_annee_actuelle > derniere_annee:
                    derniere_annee = derniere_annee_actuelle
                    noms = [experience.nom_institut]
                else:
                    noms.append(experience.nom_institut)

        if noms:
            return DerniersEtablissementsSuperieursCommunauteFrancaiseFrequentesDTO(annee=derniere_annee, noms=noms)
