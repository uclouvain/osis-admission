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
from typing import List, Optional

from admission.ddd.projet_doctoral.validation.domain.model.demande import Demande, DemandeIdentity
from admission.ddd.projet_doctoral.validation.dtos import DemandeDTO, DemandeRechercheDTO
from admission.ddd.projet_doctoral.validation.repository.i_demande import IDemandeRepository
from admission.ddd.projet_doctoral.validation.test.factory.demande import (
    DemandeAdmissionSC3DPMinimaleFactory,
    DemandePreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory,
    DemandeAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory,
)
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


class DemandeInMemoryRepository(InMemoryGenericRepository, IDemandeRepository):
    entities: List[Demande] = list()
    dtos: List[DemandeRechercheDTO] = list()

    @classmethod
    def search_dto(
        cls,
        etat_cdd: Optional[str] = '',
        etat_sic: Optional[str] = '',
        entity_ids: Optional[List['DemandeIdentity']] = None,
        **kwargs,
    ) -> List['DemandeDTO']:

        returned = cls.entities

        # Filter the entities
        if etat_cdd:
            returned = filter(lambda d: d.statut_cdd.name == etat_cdd, returned)
        if etat_sic:
            returned = filter(lambda d: d.statut_sic.name == etat_sic, returned)
        if entity_ids:
            returned = filter(lambda d: d.entity_id in entity_ids, returned)

        # Build the list of DTOs
        return [cls.get_dto(entity.entity_id) for entity in returned]

    @classmethod
    def search(cls, entity_ids: Optional[List['DemandeIdentity']] = None, **kwargs) -> List['Demande']:
        return [e for e in cls.entities if e.entity_id in entity_ids]

    @classmethod
    def reset(cls):
        cls.entities = [
            DemandeAdmissionSC3DPMinimaleFactory(),
            DemandePreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory(),
            DemandeAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory(),
        ]

    @classmethod
    def get_dto(cls, entity_id) -> DemandeDTO:
        demande = cls.search(entity_ids=[entity_id])[0]

        return DemandeDTO(
            uuid=demande.entity_id.uuid,
            statut_cdd=demande.statut_cdd and demande.statut_cdd.name or '',
            statut_sic=demande.statut_sic and demande.statut_sic.name or '',
            pre_admission_acceptee_le=demande.pre_admission_acceptee_le,
            admission_acceptee_le=demande.admission_acceptee_le,
            derniere_modification=demande.pre_admission_acceptee_le,
        )
