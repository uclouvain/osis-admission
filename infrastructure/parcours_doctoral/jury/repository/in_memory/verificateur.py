# ##############################################################################
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
# ##############################################################################
from typing import List

from admission.ddd.parcours_doctoral.jury.domain.model.jury import Jury, JuryIdentity
from admission.ddd.parcours_doctoral.jury.domain.model.verificateurs import Verificateur
from admission.ddd.parcours_doctoral.jury.dtos.jury import JuryDTO, MembreJuryDTO
from admission.ddd.parcours_doctoral.jury.dtos.verificateur import VerificateurDTO
from admission.ddd.parcours_doctoral.jury.repository.i_jury import IJuryRepository
from admission.ddd.parcours_doctoral.jury.repository.i_verificateur import IVerificateurRepository
from admission.ddd.parcours_doctoral.jury.test.factory.jury import JuryFactory, MembreJuryFactory
from admission.ddd.parcours_doctoral.jury.validator.exceptions import (
    JuryNonTrouveException,
    MembreNonTrouveDansJuryException,
)
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


class VerificateurInMemoryRepository(InMemoryGenericRepository, IVerificateurRepository):
    entities: List[Jury] = list()

    @classmethod
    def reset(cls):
        cls.entities = [
            VerificateurFactory(),
        ]

    @classmethod
    def save_list(cls, entities: List['Verificateur']) -> List['VerificateurIdentity']:
        cls.entities = entities
        return cls.get_all_identities()

    @classmethod
    def get_list(cls) -> List[Verificateur]:
        return cls.entities

    @classmethod
    def get_list_dto(cls) -> List[VerificateurDTO]:
        return [cls._load_verificateur_dto(verificateur) for verificateur in cls.get_list()]

    @classmethod
    def _load_verificateur_dto(cls, verificateur: Verificateur) -> VerificateurDTO:
        return VerificateurDTO(
            uuid=verificateur.entity_id.uuid,
            entite_ucl_id=str(verificateur.entite_ucl_id),
            matricule=verificateur.matricule,
        )
