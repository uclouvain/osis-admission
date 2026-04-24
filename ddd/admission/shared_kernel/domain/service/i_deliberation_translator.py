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

from ddd.logic.deliberation.cloture.dto.deliberation import DeliberationCycleDTO, DeliberationProgrammeAnnuelDTO
from ddd.logic.deliberation.shared_kernel.dto.progression_potentielle_etudiant_deliberation import (
    ProgressionPotentielleEtudiantDeliberationDTO,
)
from osis_common.ddd import interface


class IDeliberationTranslator(interface.DomainService):
    @classmethod
    @abstractmethod
    def recuperer_deliberations_cycles(
        cls,
        nomas: list[str],
        annee: int | None = None,
        sigle_formation: str | None = None,
    ) -> dict[tuple[str, str], DeliberationCycleDTO]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def recuperer_deliberations_annuelles(
        cls,
        nomas: list[str],
        annee: int,
    ) -> dict[tuple[str, str], dict[int, DeliberationProgrammeAnnuelDTO | None]]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def recuperer_sessions_avec_deliberations_finalisees(
        cls,
        noma: str,
        annee: int,
        sigle_formation: str,
    ) -> set[int]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def recuperer_progressions_potentielles_troisieme_session(
        cls,
        noma: str,
        annee: int,
        sigle_formation: str,
    ) -> list[ProgressionPotentielleEtudiantDeliberationDTO]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def recuperer_date_debut_periode_deliberation_deuxieme_session(
        cls,
        annee: int,
    ) -> datetime.date:
        raise NotImplementedError
