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
from typing import Dict, List, Optional

from admission.ddd.admission.shared_kernel.domain.model.proposition import PropositionIdentity
from ddd.logic.condition_acces.domain.model.titre_acces_selectionnable import TitreAccesSelectionnable
from ddd.logic.condition_acces.dtos.titre_acces_selectionnable import TitreAccesSelectionnableDTO
from ddd.logic.shared_kernel.profil.domain.service.i_parcours_interne import IExperienceParcoursInterneTranslator
from osis_common.ddd import interface


class ITitreAccesTranslator(interface.DomainService):
    @classmethod
    @abstractmethod
    def search_dto_by_proposition(
        cls,
        proposition_identity: PropositionIdentity,
        experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
        seulement_selectionnes: Optional[bool] = None,
    ) -> Dict[str, TitreAccesSelectionnableDTO]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def search_by_proposition(
        cls,
        proposition_identity: PropositionIdentity,
        experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
        seulement_selectionnes: Optional[bool] = None,
    ) -> List[TitreAccesSelectionnable]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def save(cls, entity: TitreAccesSelectionnable) -> None:
        raise NotImplementedError
