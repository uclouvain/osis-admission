# ##############################################################################
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
# ##############################################################################
from typing import List

from admission.ddd.preparation.projet_doctoral.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.preparation.projet_doctoral.domain.model.groupe_de_supervision import GroupeDeSupervision
from admission.ddd.preparation.projet_doctoral.domain.model.proposition import PropositionIdentity
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import GroupeDeSupervisionNonTrouveException
from admission.ddd.preparation.projet_doctoral.dtos import CotutelleDTO
from admission.ddd.preparation.projet_doctoral.repository.i_groupe_de_supervision import IGroupeDeSupervisionRepository
from admission.ddd.preparation.projet_doctoral.test.factory.groupe_de_supervision import (
    GroupeDeSupervisionSC3DPAvecMembresInvitesFactory,
    GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtPropositionIncompleteFactory,
    GroupeDeSupervisionSC3DPAvecPromoteurEtMembreFactory,
    GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtCotutelleFactory,
    GroupeDeSupervisionSC3DPFactory,
    GroupeDeSupervisionSC3DPSansCotutelleFactory,
)
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


class GroupeDeSupervisionInMemoryRepository(InMemoryGenericRepository, IGroupeDeSupervisionRepository):
    entities = []  # type: List[GroupeDeSupervision]

    @classmethod
    def reset(cls):
        cls.entities = [
            GroupeDeSupervisionSC3DPFactory(),
            GroupeDeSupervisionSC3DPSansCotutelleFactory(),
            GroupeDeSupervisionSC3DPAvecPromoteurEtMembreFactory(),
            GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtCotutelleFactory(),
            GroupeDeSupervisionSC3DPAvecMembresInvitesFactory(),
            GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtPropositionIncompleteFactory(),
        ]

    @classmethod
    def get_by_proposition_id(cls, proposition_id: 'PropositionIdentity') -> 'GroupeDeSupervision':
        try:
            return next(e for e in cls.entities if e.proposition_id == proposition_id)
        except StopIteration:
            raise GroupeDeSupervisionNonTrouveException

    @classmethod
    def get_cotutelle_dto(cls, uuid_proposition: str) -> 'CotutelleDTO':
        proposition_id = PropositionIdentityBuilder.build_from_uuid(uuid_proposition)
        groupe = cls.get_by_proposition_id(proposition_id=proposition_id)
        return CotutelleDTO(
            cotutelle=groupe.cotutelle and bool(groupe.cotutelle.motivation),
            motivation=groupe.cotutelle.motivation,
            institution=groupe.cotutelle.institution,
            demande_ouverture=groupe.cotutelle.demande_ouverture,
            convention=groupe.cotutelle.convention,
            autres_documents=groupe.cotutelle.autres_documents,
        )
