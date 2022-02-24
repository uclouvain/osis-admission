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
from admission.ddd.preparation.projet_doctoral.dtos import PropositionCandidatDTO, PropositionDTO
from osis_common.ddd import interface
from osis_common.ddd.interface import ApplicationService


class IPropositionRepository(interface.AbstractRepository):
    @classmethod
    @abc.abstractmethod
    def get(cls, entity_id: 'PropositionIdentity') -> 'Proposition':  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_dto(cls, entity_id: 'PropositionIdentity') -> 'PropositionDTO':  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def search(  # type: ignore[override]
            cls,
            entity_ids: Optional[List['PropositionIdentity']] = None,
            matricule_candidat: str = None,
            **kwargs
    ) -> List['Proposition']:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def search_dto(
            cls,
            numero: Optional[str] = '',
            matricule_candidat: Optional[str] = '',
            etat: Optional[str] = '',
            nationalite: Optional[str] = '',
            type: Optional[str] = '',
            commission_proximite: Optional[str] = '',
            annee_academique: Optional[int] = None,
            sigle_formation: Optional[str] = '',
            financement: Optional[str] = '',
            matricule_promoteur: Optional[str] = '',
            cotutelle: Optional[bool] = None,
    ) -> List['PropositionCandidatDTO']:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete(cls, entity_id: 'PropositionIdentity', **kwargs: ApplicationService) -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def save(cls, entity: 'Proposition') -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_next_reference(cls):
        raise NotImplementedError
