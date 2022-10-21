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

from admission.ddd.admission.doctorat.preparation.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    GroupeDeSupervisionIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.dtos import CotutelleDTO
from admission.ddd.parcours_doctoral.domain.model.doctorat import DoctoratIdentity
from osis_common.ddd import interface
from osis_common.ddd.interface import ApplicationService


class IGroupeDeSupervisionRepository(interface.AbstractRepository):
    @classmethod
    @abc.abstractmethod
    def get(cls, entity_id: 'GroupeDeSupervisionIdentity') -> 'GroupeDeSupervision':  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_by_proposition_id(cls, proposition_id: 'PropositionIdentity') -> 'GroupeDeSupervision':
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_by_doctorat_id(cls, doctorat_id: 'DoctoratIdentity') -> 'GroupeDeSupervision':
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def search(  # type: ignore[override]
        cls,
        entity_ids: Optional[List['GroupeDeSupervisionIdentity']] = None,
        matricule_membre: str = None,
        **kwargs,
    ) -> List['GroupeDeSupervision']:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete(  # type: ignore[override]
        cls,
        entity_id: 'GroupeDeSupervisionIdentity',
        **kwargs: ApplicationService,
    ) -> None:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def save(cls, entity: 'GroupeDeSupervision') -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_cotutelle_dto(cls, uuid_proposition: str) -> 'CotutelleDTO':
        raise NotImplementedError
