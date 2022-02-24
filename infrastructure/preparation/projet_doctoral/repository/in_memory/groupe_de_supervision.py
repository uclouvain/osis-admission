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
from typing import List, Optional

from admission.ddd.preparation.projet_doctoral.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.preparation.projet_doctoral.domain.model._cotutelle import pas_de_cotutelle
from admission.ddd.preparation.projet_doctoral.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    GroupeDeSupervisionIdentity,
)
from admission.ddd.preparation.projet_doctoral.domain.model.proposition import PropositionIdentity
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import GroupeDeSupervisionNonTrouveException
from admission.ddd.preparation.projet_doctoral.dtos import CotutelleDTO
from admission.ddd.preparation.projet_doctoral.repository.i_groupe_de_supervision import IGroupeDeSupervisionRepository
from admission.ddd.preparation.projet_doctoral.test.factory.groupe_de_supervision import (
    GroupeDeSupervisionSC3DPAvecMembresInvitesFactory,
    GroupeDeSupervisionSC3DPAvecPromoteurDejaApprouveEtAutrePromoteurFactory,
    GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtCotutelleFactory,
    GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtFinancementIncompletFactory,
    GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtProjetIncompletFactory,
    GroupeDeSupervisionSC3DPAvecPromoteurEtMembreFactory,
    GroupeDeSupervisionSC3DPCotutelleAvecPromoteurExterneFactory,
    GroupeDeSupervisionSC3DPCotutelleIndefinieFactory,
    GroupeDeSupervisionSC3DPCotutelleSansPromoteurExterneFactory,
    GroupeDeSupervisionSC3DPFactory,
    GroupeDeSupervisionSC3DPPreAdmissionFactory,
    GroupeDeSupervisionSC3DPSansMembresCAFactory,
    GroupeDeSupervisionSC3DPSansPromoteurFactory,
    GroupeDeSupervisionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
)
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


class GroupeDeSupervisionInMemoryRepository(InMemoryGenericRepository, IGroupeDeSupervisionRepository):
    entities = []  # type: List[GroupeDeSupervision]

    @classmethod
    def reset(cls):
        cls.entities = [
            GroupeDeSupervisionSC3DPFactory(),
            GroupeDeSupervisionSC3DPPreAdmissionFactory(),
            GroupeDeSupervisionSC3DPCotutelleIndefinieFactory(),
            GroupeDeSupervisionSC3DPAvecPromoteurEtMembreFactory(),
            GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtCotutelleFactory(),
            GroupeDeSupervisionSC3DPAvecMembresInvitesFactory(),
            GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtProjetIncompletFactory(),
            GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtFinancementIncompletFactory(),
            GroupeDeSupervisionSC3DPCotutelleAvecPromoteurExterneFactory(),
            GroupeDeSupervisionSC3DPCotutelleSansPromoteurExterneFactory(),
            GroupeDeSupervisionSC3DPSansPromoteurFactory(),
            GroupeDeSupervisionSC3DPSansMembresCAFactory(),
            GroupeDeSupervisionSC3DPAvecPromoteurDejaApprouveEtAutrePromoteurFactory(),
            GroupeDeSupervisionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(),
        ]

    @classmethod
    def search(
            cls,
            entity_ids: Optional[List['GroupeDeSupervisionIdentity']] = None,
            matricule_membre: str = None,
            **kwargs
    ) -> List['GroupeDeSupervision']:
        if matricule_membre:
            return [
                e for e in cls.entities
                if any(s.promoteur_id for s in e.signatures_promoteurs if s.promoteur_id.matricule == matricule_membre)
                or any(s.membre_CA_id for s in e.signatures_membres_CA if s.membre_CA_id.matricule == matricule_membre)
            ]
        raise NotImplementedError

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
            cotutelle=None if groupe.cotutelle is None else groupe.cotutelle != pas_de_cotutelle,
            motivation=groupe.cotutelle and groupe.cotutelle.motivation or '',
            institution=groupe.cotutelle and groupe.cotutelle.institution or '',
            demande_ouverture=groupe.cotutelle and groupe.cotutelle.demande_ouverture or [],
            convention=groupe.cotutelle and groupe.cotutelle.convention or [],
            autres_documents=groupe.cotutelle and groupe.cotutelle.autres_documents or [],
        )
