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
from abc import abstractmethod
from typing import List, Dict

from admission.ddd.admission.domain.model.bourse import BourseIdentity
from admission.ddd.admission.dtos.bourse import BourseDTO
from osis_common.ddd import interface


class IBourseTranslator(interface.DomainService):
    @classmethod
    @abstractmethod
    def get(cls, uuid: str) -> BourseIdentity:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_dto(cls, uuid: str) -> BourseDTO:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def search(cls, uuids: List[str]) -> Dict[str, BourseIdentity]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def search_dto(cls, entity_ids: BourseIdentity) -> Dict[str, BourseDTO]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def verifier_existence(cls, uuid: str) -> bool:
        raise NotImplementedError
