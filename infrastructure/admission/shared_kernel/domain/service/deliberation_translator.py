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
from collections import defaultdict
from typing import Optional

from admission.ddd.admission.shared_kernel.domain.deliberation import DecisionDeliberation
from admission.ddd.admission.shared_kernel.domain.service.i_deliberation_translator import IDeliberationTranslator
from ddd.logic.deliberation.cloture.domain.validator.exceptions import DecisionDeliberationNonTrouveeException
from ddd.logic.deliberation.cloture.dto.deliberation import (
    DecisionDeliberationDTO,
    DeliberationCycleDTO,
    DeliberationProgrammeAnnuelDTO,
)
from ddd.logic.deliberation.cloture.queries import (
    RechercherDeliberationCycleQuery,
    RechercherDeliberationsProgrammesAnnuelsActeesQuery,
    RecupererDecisionDeliberationQuery,
)
from ddd.logic.deliberation.shared_kernel.dto.calendrier_academique import PeriodeDeliberationDTO
from ddd.logic.deliberation.shared_kernel.queries import GetPeriodeDeliberationQuery
from epc.models.enums.reussite_bloc1 import ReussiteBloc1


class DeliberationTranslator(IDeliberationTranslator):
    @classmethod
    def recuperer_deliberations_cycles(
        cls,
        nomas: list[str],
        annee: int | None = None,
        sigle_formation: str | None = None,
    ) -> dict[tuple[str, str], DeliberationCycleDTO]:
        from infrastructure.messages_bus import message_bus_instance

        cycles_deliberations: list[DeliberationCycleDTO] = message_bus_instance.invoke(
            RechercherDeliberationCycleQuery(nomas=nomas, annee=annee, sigle_formation=sigle_formation)
        )

        return {
            (deliberation.noma, deliberation.sigle_formation): deliberation for deliberation in cycles_deliberations
        }

    @classmethod
    def recuperer_deliberations_annuelles(
        cls,
        nomas: list[str],
        annee: int,
        sigle_formation: str = '',
    ) -> dict[tuple[str, str], dict[int, DeliberationProgrammeAnnuelDTO | None]]:
        from infrastructure.messages_bus import message_bus_instance

        annual_deliberations: list[DeliberationProgrammeAnnuelDTO] = message_bus_instance.invoke(
            RechercherDeliberationsProgrammesAnnuelsActeesQuery(
                nomas=nomas,
                annee=annee,
                sigle_formation=sigle_formation,
            )
        )

        annual_deliberations_dict: dict[tuple[str, str], dict[int, DeliberationProgrammeAnnuelDTO | None]] = (
            defaultdict(dict)
        )
        for deliberation in annual_deliberations:
            deliberation_id = (deliberation.noma, deliberation.sigle_formation)
            annual_deliberations_dict[deliberation_id][deliberation.numero_session] = deliberation

        return annual_deliberations_dict

    @classmethod
    def recuperer_date_debut_periode_deliberation_deuxieme_session(
        cls,
        annee: int,
    ) -> datetime.date:
        from infrastructure.messages_bus import message_bus_instance

        periode_deliberation: PeriodeDeliberationDTO = message_bus_instance.invoke(
            GetPeriodeDeliberationQuery(
                annee=annee,
                numero_session=2,
            )
        )

        return periode_deliberation.date_debut

    @classmethod
    def recuperer_decision_deliberation(
        cls,
        noma: str,
        sigle_formation: str,
        annee: Optional[int] = None,
    ) -> DecisionDeliberation | None:
        from infrastructure.messages_bus import message_bus_instance

        if not noma:
            return None

        try:
            decision_deliberation: 'DecisionDeliberationDTO' = message_bus_instance.invoke(
                RecupererDecisionDeliberationQuery(
                    noma=noma,
                    sigle_formation=sigle_formation,
                    annee=annee,
                )
            )
        except DecisionDeliberationNonTrouveeException:
            return DecisionDeliberation(
                est_diplome=False,
                reussite_bloc_1=False,
            )

        return DecisionDeliberation(
            est_diplome=decision_deliberation.est_diplome,
            reussite_bloc_1=(
                True if decision_deliberation.reussite_bloc_1 == ReussiteBloc1.REUSSITE_BLOC1.name else False
            ),
        )
