# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

import uuid
from typing import List, Optional, Union

from admission.contrib.models.enums.actor_type import ActorType
from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.domain.model._cotutelle import pas_de_cotutelle
from admission.ddd.admission.doctorat.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.admission.doctorat.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.admission.doctorat.preparation.domain.model._signature_membre_CA import SignatureMembreCA
from admission.ddd.admission.doctorat.preparation.domain.model._signature_promoteur import SignaturePromoteur
from admission.ddd.admission.doctorat.preparation.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    GroupeDeSupervisionIdentity,
    SignataireIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    GroupeDeSupervisionNonTrouveException,
)
from admission.ddd.admission.doctorat.preparation.dtos import CotutelleDTO, MembreCADTO, PromoteurDTO
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.doctorat.preparation.test.factory.groupe_de_supervision import (
    GroupeDeSupervisionPreSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    GroupeDeSupervisionSC3DPAvecMembresInvitesFactory,
    GroupeDeSupervisionSC3DPAvecPromoteurDejaApprouveEtAutrePromoteurFactory,
    GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtCotutelleFactory,
    GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtFinancementIncompletFactory,
    GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtProjetIncompletFactory,
    GroupeDeSupervisionSC3DPAvecPromoteurEtMembreFactory,
    GroupeDeSupervisionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory,
    GroupeDeSupervisionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    GroupeDeSupervisionSC3DPCotutelleAvecPromoteurExterneFactory,
    GroupeDeSupervisionSC3DPCotutelleIndefinieFactory,
    GroupeDeSupervisionSC3DPCotutelleSansPromoteurExterneFactory,
    GroupeDeSupervisionSC3DPFactory,
    GroupeDeSupervisionSC3DPPreAdmissionFactory,
    GroupeDeSupervisionSC3DPSansMembresCAFactory,
    GroupeDeSupervisionSC3DPSansPromoteurFactory,
    GroupeDeSupervisionSC3DPSansPromoteurReferenceFactory,
    GroupeDeSupervisionConfirmeeSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
)
from admission.ddd.parcours_doctoral.domain.model.doctorat import DoctoratIdentity
from admission.infrastructure.admission.doctorat.preparation.domain.service.in_memory.membre_CA import (
    MembreCA,
    MembreCAInMemoryTranslator,
)
from admission.infrastructure.admission.doctorat.preparation.domain.service.in_memory.promoteur import (
    Promoteur,
    PromoteurInMemoryTranslator,
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
            GroupeDeSupervisionSC3DPSansPromoteurReferenceFactory(),
            GroupeDeSupervisionSC3DPSansMembresCAFactory(),
            GroupeDeSupervisionSC3DPAvecPromoteurDejaApprouveEtAutrePromoteurFactory(),
            GroupeDeSupervisionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(),
            GroupeDeSupervisionPreSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(),
            GroupeDeSupervisionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory(),
            GroupeDeSupervisionConfirmeeSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(),
        ]

    @classmethod
    def search(
        cls, entity_ids: Optional[List['GroupeDeSupervisionIdentity']] = None, matricule_membre: str = None, **kwargs
    ) -> List['GroupeDeSupervision']:
        if matricule_membre:
            return [
                e
                for e in cls.entities
                if any(s.promoteur_id for s in e.signatures_promoteurs if s.promoteur_id.uuid == matricule_membre)
                or any(s.membre_CA_id for s in e.signatures_membres_CA if s.membre_CA_id.uuid == matricule_membre)
            ]
        raise NotImplementedError

    @classmethod
    def get_by_proposition_id(cls, proposition_id: 'PropositionIdentity') -> 'GroupeDeSupervision':
        try:
            return next(e for e in cls.entities if e.proposition_id == proposition_id)
        except StopIteration:
            raise GroupeDeSupervisionNonTrouveException

    @classmethod
    def get_by_doctorat_id(cls, doctorat_id: 'DoctoratIdentity') -> 'GroupeDeSupervision':
        return cls.get_by_proposition_id(PropositionIdentityBuilder.build_from_uuid(doctorat_id.uuid))

    @classmethod
    def get_cotutelle_dto(cls, uuid_proposition: str) -> 'CotutelleDTO':
        proposition_id = PropositionIdentityBuilder.build_from_uuid(uuid_proposition)
        groupe = cls.get_by_proposition_id(proposition_id=proposition_id)
        return CotutelleDTO(
            cotutelle=None if groupe.cotutelle is None else groupe.cotutelle != pas_de_cotutelle,
            motivation=groupe.cotutelle and groupe.cotutelle.motivation or '',
            institution_fwb=groupe.cotutelle and groupe.cotutelle.institution_fwb or None,
            institution=groupe.cotutelle and groupe.cotutelle.institution or '',
            demande_ouverture=groupe.cotutelle and groupe.cotutelle.demande_ouverture or [],
            convention=groupe.cotutelle and groupe.cotutelle.convention or [],
            autres_documents=groupe.cotutelle and groupe.cotutelle.autres_documents or [],
            autre_institution=True if groupe.cotutelle and groupe.cotutelle.autre_institution_nom else False,
            autre_institution_nom=groupe.cotutelle and groupe.cotutelle.autre_institution_nom or '',
            autre_institution_adresse=groupe.cotutelle and groupe.cotutelle.autre_institution_adresse or '',
        )

    @classmethod
    def add_member(
        cls,
        groupe_id: 'GroupeDeSupervisionIdentity',
        type: ActorType,
        matricule: Optional[str] = '',
        first_name: Optional[str] = '',
        last_name: Optional[str] = '',
        email: Optional[str] = '',
        is_doctor: bool = False,
        institute: Optional[str] = '',
        city: Optional[str] = '',
        country_code: Optional[str] = '',
        language: Optional[str] = '',
    ) -> 'SignataireIdentity':
        groupe: GroupeDeSupervision = cls.get(groupe_id)
        if type == ActorType.PROMOTER:
            signataire_id = PromoteurIdentity(str(uuid.uuid4()))
            groupe.signatures_promoteurs.append(SignaturePromoteur(promoteur_id=signataire_id))
            PromoteurInMemoryTranslator.promoteurs.append(
                Promoteur(
                    signataire_id,
                    matricule=matricule,
                    nom=last_name,
                    prenom=first_name,
                    email=email,
                    est_docteur=is_doctor,
                    institution=institute,
                    ville=city,
                    pays=country_code,
                )
            )
        else:
            signataire_id = MembreCAIdentity(str(uuid.uuid4()))
            groupe.signatures_membres_CA.append(SignatureMembreCA(membre_CA_id=signataire_id))
            MembreCAInMemoryTranslator.membres_CA.append(
                MembreCA(
                    signataire_id,
                    matricule=matricule,
                    nom=last_name,
                    prenom=first_name,
                    email=email,
                    est_docteur=is_doctor,
                    institution=institute,
                    ville=city,
                    pays=country_code,
                )
            )
        return signataire_id

    @classmethod
    def remove_member(cls, groupe_id: 'GroupeDeSupervisionIdentity', signataire: 'SignataireIdentity') -> None:
        groupe: GroupeDeSupervision = cls.get(groupe_id)
        if isinstance(signataire, PromoteurIdentity):
            groupe.signatures_promoteurs = [s for s in groupe.signatures_promoteurs if s.promoteur_id != signataire]
        else:
            groupe.signatures_membres_CA = [s for s in groupe.signatures_membres_CA if s.membre_CA_id != signataire]

    @classmethod
    def get_members(cls, groupe_id: 'GroupeDeSupervisionIdentity') -> List[Union['PromoteurDTO', 'MembreCADTO']]:
        members = []
        groupe: GroupeDeSupervision = cls.get(groupe_id)
        for membre in groupe.signatures_promoteurs:
            members.append(PromoteurInMemoryTranslator.get_dto(membre.promoteur_id))
        for membre in groupe.signatures_membres_CA:
            members.append(MembreCAInMemoryTranslator.get_dto(membre.membre_CA_id))
        return members

    @classmethod
    def edit_external_member(
        cls,
        groupe_id: 'GroupeDeSupervisionIdentity',
        membre_id: 'SignataireIdentity',
        first_name: Optional[str] = '',
        last_name: Optional[str] = '',
        email: Optional[str] = '',
        is_doctor: Optional[bool] = False,
        institute: Optional[str] = '',
        city: Optional[str] = '',
        country_code: Optional[str] = '',
        language: Optional[str] = '',
    ) -> None:
        for membre in PromoteurInMemoryTranslator.promoteurs + MembreCAInMemoryTranslator.membres_CA:
            if membre.id == membre_id:
                membre.prenom = first_name
                membre.nom = last_name
                membre.email = email
                membre.est_docteur = is_doctor
                membre.institution = institute
                membre.ville = city
                membre.pays = country_code
                membre.langue = language
                return
