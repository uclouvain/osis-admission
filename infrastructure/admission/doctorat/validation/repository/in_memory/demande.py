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

from admission.ddd.admission.doctorat.validation.domain.model.demande import Demande, DemandeIdentity
from admission.ddd.admission.doctorat.validation.domain.validator.exceptions import DemandeNonTrouveeException
from admission.ddd.admission.doctorat.validation.dtos import DemandeDTO, DemandeRechercheDTO, ProfilCandidatDTO
from admission.ddd.admission.doctorat.validation.repository.i_demande import IDemandeRepository
from admission.ddd.admission.doctorat.validation.test.factory.demande import (
    DemandeAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory,
    DemandeAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    DemandeAdmissionSC3DPMinimaleFactory,
    DemandePreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory,
)
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


class DemandeInMemoryRepository(InMemoryGenericRepository, IDemandeRepository):
    entities: List[Demande] = list()
    dtos: List[DemandeRechercheDTO] = list()

    countries = {
        'BE': 'Belgium',
        'FR': 'France',
    }

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
        return [cls._load_dto(demande) for demande in returned]

    @classmethod
    def search(cls, entity_ids: Optional[List['DemandeIdentity']] = None, **kwargs) -> List['Demande']:
        return [e for e in cls.entities if e.entity_id in entity_ids]

    @classmethod
    def reset(cls):
        cls.entities = [
            DemandeAdmissionSC3DPMinimaleFactory(),
            DemandePreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory(),
            DemandeAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory(),
            DemandeAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(),
        ]

    @classmethod
    def get(cls, entity_id: 'DemandeIdentity') -> 'Demande':
        proposition = super().get(entity_id)
        if not proposition:
            raise DemandeNonTrouveeException
        return proposition

    @classmethod
    def get_dto(cls, entity_id) -> DemandeDTO:
        demande = cls.get(entity_id=entity_id)
        return cls._load_dto(demande)

    @classmethod
    def _load_dto(cls, demande: Demande) -> DemandeDTO:
        return DemandeDTO(
            uuid=demande.entity_id.uuid,
            statut_cdd=demande.statut_cdd and demande.statut_cdd.name or '',
            statut_sic=demande.statut_sic and demande.statut_sic.name or '',
            pre_admission_confirmee_le=demande.pre_admission_confirmee_le,
            admission_confirmee_le=demande.admission_confirmee_le,
            pre_admission_acceptee_le=demande.pre_admission_acceptee_le,
            admission_acceptee_le=demande.admission_acceptee_le,
            derniere_modification=demande.modifiee_le,
            profil_candidat=ProfilCandidatDTO(
                prenom=demande.profil_candidat.prenom,
                nom=demande.profil_candidat.nom,
                genre=demande.profil_candidat.genre,
                nationalite=demande.profil_candidat.nationalite,
                nom_pays_nationalite=cls.countries.get(demande.profil_candidat.nationalite, ''),
                email=demande.profil_candidat.email,
                pays=demande.profil_candidat.pays,
                nom_pays=cls.countries.get(demande.profil_candidat.pays, ''),
                code_postal=demande.profil_candidat.code_postal,
                ville=demande.profil_candidat.ville,
                lieu_dit=demande.profil_candidat.lieu_dit,
                rue=demande.profil_candidat.rue,
                numero_rue=demande.profil_candidat.numero_rue,
                boite_postale=demande.profil_candidat.boite_postale,
            ),
        )
