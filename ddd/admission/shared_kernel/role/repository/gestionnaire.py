##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
from abc import abstractmethod
from typing import List, Optional

from admission.ddd.admission.dtos.formation import BaseFormationDTO
from osis_common.ddd import interface
from osis_common.ddd.interface import EntityIdentity, RootEntity


class IGestionnaireRepository(interface.AbstractRepository):
    @classmethod
    def get(cls, entity_id: EntityIdentity) -> RootEntity:
        """
        Function used to get root entity by entity identity.
        :return: The root entity
        """
        raise NotImplementedError

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[RootEntity]:
        """
        Function used to search multiple root entity (by entity identity for ex).
        :return: The list of root entities found
        """
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs) -> None:
        """
        Function used to delete a root entity via it's entity identity.
        """
        raise NotImplementedError

    @classmethod
    def save(cls, entity: RootEntity) -> None:
        """
        Function used to persist existing domain RootEntity (aggregate) into the database.
        :param entity: Any domain root entity.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def rechercher_formations_gerees(
        cls,
        matriculaire_gestionnaire: str,
        annee: int,
        terme_recherche: str,
    ) -> List['BaseFormationDTO']:
        raise NotImplementedError
