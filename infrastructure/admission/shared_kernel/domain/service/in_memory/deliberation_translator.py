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
from typing import Optional

from admission.ddd.admission.shared_kernel.domain.deliberation import DecisionDeliberation
from admission.ddd.admission.shared_kernel.domain.service.i_deliberation_translator import IDeliberationTranslator
from ddd.logic.deliberation.cloture.dto.deliberation import DeliberationCycleDTO, DeliberationProgrammeAnnuelDTO


class DeliberationInMemoryTranslator(IDeliberationTranslator):
    @classmethod
    def recuperer_deliberations_cycles(
        cls,
        nomas: list[str],
        annee: int | None = None,
        sigle_formation: str | None = None,
    ) -> dict[tuple[str, str], DeliberationCycleDTO]:
        return {}

    @classmethod
    def recuperer_deliberations_annuelles(
        cls,
        nomas: list[str],
        annee: int,
        sigle_formation: str = '',
    ) -> dict[tuple[str, str], dict[int, DeliberationProgrammeAnnuelDTO | None]]:
        return {}

    @classmethod
    def recuperer_date_debut_periode_deliberation_deuxieme_session(
        cls,
        annee: int,
    ) -> datetime.date:
        return datetime.date(year=annee, month=4, day=15)

    @classmethod
    def recuperer_decision_deliberation(
        cls,
        noma: str,
        sigle_formation: str,
        annee: Optional[int] = None,
    ) -> DecisionDeliberation | None:
        return DecisionDeliberation(
            est_diplome=False,
            reussite_bloc_1=False,
        )
