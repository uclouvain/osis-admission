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
from typing import List, Optional

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import DoctoratIdentity
from admission.ddd.admission.repository.i_proposition import IGlobalPropositionRepository
from osis_common.ddd.interface import ApplicationService, EntityIdentity, RootEntity


class IDoctoratRepository(IGlobalPropositionRepository):
    @classmethod
    def get(cls, entity_id: 'DoctoratIdentity') -> 'Doctorat':  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def save(cls, entity: 'Doctorat') -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        raise NotImplementedError

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[RootEntity]:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def verifier_existence(cls, entity_id: 'DoctoratIdentity') -> None:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_dto(cls, entity_id: 'DoctoratIdentity') -> 'DoctoratDTO':  # type: ignore[override]
        raise NotImplementedError
