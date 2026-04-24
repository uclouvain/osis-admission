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
from abc import abstractmethod
from typing import Optional, Tuple

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition as PropositionDoctorat
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition as PropositionGeneral
from admission.ddd.admission.shared_kernel.domain.service.i_calcul_condition_acces_translator import (
    ICalculConditionAccesTranslator,
)
from ddd.logic.condition_acces.domain.model.titre_acces import TitreAcces
from ddd.logic.condition_acces.dtos.condition_acces import ConditionAccesDTO
from ddd.logic.condition_acces.queries import CalculerConditionDAccesQuery


class CalculConditionAccesTranslator(ICalculConditionAccesTranslator):
    @classmethod
    def calculer_condition_d_acces(
        cls,
        proposition: PropositionDoctorat | PropositionGeneral,
    ) -> Optional[ConditionAccesDTO]:
        from infrastructure.messages_bus import message_bus_instance

        return message_bus_instance.invoke(
            CalculerConditionDAccesQuery(
                matricule=proposition.matricule_candidat,
                sigle_formation=proposition.formation_id.sigle,
                annee=proposition.formation_id.annee,
            ),
        )

    @classmethod
    def determiner_titre_et_condition_d_acces(
        cls,
        proposition: PropositionDoctorat | PropositionGeneral,
    ) -> Optional[Tuple[TitreAcces, ConditionAccesDTO]]:
        # TODO
