##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import abc
from typing import List, Optional

from admission.ddd.preparation.projet_doctoral.domain.model.proposition import Proposition, PropositionIdentity
from osis_common.ddd import interface
from osis_common.ddd.interface import ApplicationService


class IPropositionRepository(interface.AbstractRepository):
    @classmethod
    @abc.abstractmethod
    def get(cls, entity_id: 'PropositionIdentity') -> 'Proposition':
        # TODO :: réutiliser get_dto() et convertir DTO en Proposition
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def search(
            cls,
            entity_ids: Optional[List['PropositionIdentity']] = None,
            matricule_candidat: str = None,
            **kwargs
    ) -> List['Proposition']:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete(cls, entity_id: 'PropositionIdentity', **kwargs: ApplicationService) -> None:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def save(cls, entity: 'Proposition') -> None:
        raise NotImplementedError
