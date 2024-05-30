# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import abc
from typing import List, Dict, Optional

from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.model.titre_acces_selectionnable import (
    TitreAccesSelectionnable,
    TitreAccesSelectionnableIdentity,
)
from admission.ddd.admission.dtos.titre_acces_selectionnable import TitreAccesSelectionnableDTO
from ddd.logic.shared_kernel.profil.domain.service.parcours_interne import IExperienceParcoursInterneTranslator
from osis_common.ddd import interface
from osis_common.ddd.interface import EntityIdentity, RootEntity


class ITitreAccesSelectionnableRepository(interface.AbstractRepository):
    @classmethod
    def get(cls, entity_id: EntityIdentity) -> RootEntity:
        raise NotImplementedError

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[RootEntity]:
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: TitreAccesSelectionnableIdentity, **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    def search_dto_by_proposition(
        cls,
        proposition_identity: PropositionIdentity,
        experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
        seulement_selectionnes: Optional[bool] = None,
    ) -> Dict[str, TitreAccesSelectionnableDTO]:
        return {
            entity.entity_id.uuid_experience: cls.entity_to_dto(entity)
            for entity in cls.search_by_proposition(
                proposition_identity,
                experience_parcours_interne_translator,
                seulement_selectionnes,
            )
        }

    @classmethod
    @abc.abstractmethod
    def search_by_proposition(
        cls,
        proposition_identity: PropositionIdentity,
        experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
        seulement_selectionnes: Optional[bool] = None,
    ) -> List[TitreAccesSelectionnable]:
        raise NotImplementedError

    @classmethod
    def entity_to_dto(cls, entity: TitreAccesSelectionnable) -> TitreAccesSelectionnableDTO:
        return TitreAccesSelectionnableDTO(
            uuid_experience=entity.entity_id.uuid_experience,
            selectionne=entity.selectionne,
            type_titre=entity.entity_id.type_titre.name,
            annee=entity.annee,
            pays_iso_code=entity.pays_iso_code,
        )
