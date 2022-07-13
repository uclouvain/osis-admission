# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Mapping, Optional

from admission.ddd.projet_doctoral.doctorat.formation.domain.model._enums import CategorieActivite
from admission.ddd.projet_doctoral.doctorat.formation.domain.model.activite import Activite, ActiviteIdentity
from admission.ddd.projet_doctoral.doctorat.formation.domain.validator.exceptions import ActiviteNonTrouvee
from admission.ddd.projet_doctoral.doctorat.formation.dtos import ActiviteDTO
from admission.ddd.projet_doctoral.doctorat.formation.repository.i_activite import IActiviteRepository
from admission.ddd.projet_doctoral.doctorat.formation.test.factory.activite import ActiviteFactory
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


class ActiviteInMemoryRepository(InMemoryGenericRepository, IActiviteRepository):
    entities: List['Activite']

    @classmethod
    def get_multiple(cls, entity_ids: List['ActiviteIdentity']) -> Mapping['ActiviteIdentity', 'Activite']:
        ret = {activite.entity_id: activite for activite in cls.entities if activite.entity_id in entity_ids}
        if len(entity_ids) != len(ret):
            raise ActiviteNonTrouvee
        return ret

    @classmethod
    def get_dto(cls, entity_id: 'ActiviteIdentity') -> ActiviteDTO:
        return next(activite._dto for activite in cls.entities if activite.entity_id == entity_id)  # pragma: no cover

    @classmethod
    def get_dtos(cls, entity_ids: List['ActiviteIdentity']) -> Mapping['ActiviteIdentity', ActiviteDTO]:
        ret = {activite.entity_id: activite._dto for activite in cls.entities if activite.entity_id in entity_ids}
        if len(entity_ids) != len(ret):
            raise ActiviteNonTrouvee
        return ret

    @classmethod
    def reset(cls):
        cls.entities = [ActiviteFactory() for _ in range(len(CategorieActivite.choices()))]

    @classmethod
    def search(cls, parent_id: Optional[ActiviteIdentity] = None, **kwargs) -> List[Activite]:
        if parent_id is not None:
            return [entity for entity in cls.entities if entity.parent_id == parent_id]
        return super().search(**kwargs)  # pragma: no cover
