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

import abc
from typing import List, Mapping, Optional

from admission.ddd.doctorat.formation.domain.model.activite import Activite, ActiviteIdentity
from admission.ddd.doctorat.formation.dtos import ActiviteDTO
from osis_common.ddd import interface


class IActiviteRepository(interface.AbstractRepository):
    @classmethod
    @abc.abstractmethod
    def get(cls, entity_id: 'ActiviteIdentity') -> 'Activite':  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_multiple(
        cls, entity_ids: List['ActiviteIdentity']
    ) -> Mapping['ActiviteIdentity', 'Activite']:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_dto(cls, entity_id: 'ActiviteIdentity') -> ActiviteDTO:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_dtos(cls, entity_ids: List['ActiviteIdentity']) -> Mapping['ActiviteIdentity', ActiviteDTO]:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete(cls, entity_id: 'ActiviteIdentity', **kwargs) -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def save(cls, entity: 'Activite') -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def search(cls, parent_id: Optional[ActiviteIdentity] = None, **kwargs) -> List[Activite]:  # type: ignore[override]
        raise NotImplementedError
