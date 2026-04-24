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

from admission.ddd.admission.shared_kernel.domain.service.i_deliberation_translator import IDeliberationTranslator
from ddd.logic.deliberation.cloture.dto.deliberation import DeliberationCycleDTO, DeliberationProgrammeAnnuelDTO
from ddd.logic.deliberation.cloture.queries import (
    RechercherDeliberationCycleQuery,
    RechercherDeliberationsProgrammesAnnuelsActeesQuery,
)
from ddd.logic.deliberation.queries import (
    ListerFinalisationDeliberationEtudiantQuery,
    ListerProgressionPotentielleEtudiantDeliberationQuery,
)
from ddd.logic.deliberation.shared_kernel.dto.calendrier_academique import PeriodeDeliberationDTO
from ddd.logic.deliberation.shared_kernel.dto.finalisation_deliberation_etudiant import (
    FinalisationDeliberationEtudiantDTO,
)
from ddd.logic.deliberation.shared_kernel.dto.progression_potentielle_etudiant_deliberation import (
    ProgressionPotentielleEtudiantDeliberationDTO,
)
from ddd.logic.deliberation.shared_kernel.queries import GetPeriodeDeliberationQuery


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
    ) -> dict[tuple[str, str], dict[int, DeliberationProgrammeAnnuelDTO | None]]:
        from infrastructure.messages_bus import message_bus_instance

        annual_deliberations: list[DeliberationProgrammeAnnuelDTO] = message_bus_instance.invoke(
            RechercherDeliberationsProgrammesAnnuelsActeesQuery(nomas=nomas, annee=annee)
        )

        annual_deliberations_dict: dict[tuple[str, str], dict[int, DeliberationProgrammeAnnuelDTO | None]] = (
            defaultdict(dict)
        )
        for deliberation in annual_deliberations:
            deliberation_id = (deliberation.noma, deliberation.sigle_formation)
            annual_deliberations_dict[deliberation_id][deliberation.numero_session] = deliberation

        return annual_deliberations_dict

    @classmethod
    def recuperer_sessions_avec_deliberations_finalisees(
        cls,
        noma: str,
        annee: int,
        sigle_formation: str,
    ) -> set[int]:
        from infrastructure.messages_bus import message_bus_instance

        try:
            finalisations_deliberations: list[FinalisationDeliberationEtudiantDTO] = message_bus_instance.invoke(
                ListerFinalisationDeliberationEtudiantQuery(
                    sigle_formation=sigle_formation,
                    nomas=[noma],
                    annee=annee,
                )
            )
        except NotImplementedError:
            return set()

        return {finalisation.numero_session for finalisation in finalisations_deliberations}

    @classmethod
    def recuperer_progressions_potentielles_troisieme_session(
        cls,
        noma: str,
        annee: int,
        sigle_formation: str,
    ) -> list[ProgressionPotentielleEtudiantDeliberationDTO]:
        from infrastructure.messages_bus import message_bus_instance

        try:
            return message_bus_instance.invoke(
                ListerProgressionPotentielleEtudiantDeliberationQuery(
                    sigle_formation=sigle_formation,
                    nomas=[noma],
                    annee=annee,
                    numero_session=3,
                )
            )
        except NotImplementedError:
            return []

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
