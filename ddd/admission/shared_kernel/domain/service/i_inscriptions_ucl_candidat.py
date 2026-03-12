# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.shared_kernel.domain.service.i_annee_inscription_formation import (
    IAnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.shared_kernel.dtos.inscription_ucl_candidat import (
    InscriptionUCLCandidatDTO,
    PeriodeReinscriptionDTO,
)
from osis_common.ddd import interface


class IInscriptionsUCLCandidatService(interface.DomainService):
    @classmethod
    @abstractmethod
    def recuperer(
        cls,
        matricule_candidat: str,
        annees: list[int] | None = None,
    ) -> list[InscriptionUCLCandidatDTO]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def est_inscrit_recemment(
        cls,
        matricule_candidat: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def est_delibere(
        cls,
        matricule_candidat: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def est_en_poursuite(
        cls,
        matricule_candidat: str,
        sigle_formation: str,
    ) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def est_diplome(
        cls,
        matricule_candidat: str,
        sigle_formation: str,
    ) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def est_en_poursuite_directe(
        cls,
        matricule_candidat: str,
        sigle_formation: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def recuperer_informations_periode_de_reinscription(
        cls,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> PeriodeReinscriptionDTO:
        raise NotImplementedError

    @classmethod
    def periode_de_reinscription_en_cours(
        cls,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> bool:
        periode_reinscription = cls.recuperer_informations_periode_de_reinscription(
            annee_inscription_formation_translator=annee_inscription_formation_translator,
        )
        today_date = datetime.date.today()
        return periode_reinscription.date_debut <= today_date <= periode_reinscription.date_fin
