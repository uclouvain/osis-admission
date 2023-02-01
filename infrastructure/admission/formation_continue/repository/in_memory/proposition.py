# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from dataclasses import dataclass
from typing import List, Optional

import factory

from admission.ddd.admission.dtos import AdressePersonnelleDTO
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.formation_continue.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_continue.dtos import PropositionDTO
from admission.ddd.admission.formation_continue.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.formation_continue.test.factory.proposition import (
    PropositionFactory,
    _PropositionIdentityFactory,
)
from admission.ddd.admission.repository.i_proposition import formater_reference
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.formation_continue.domain.service.in_memory.formation import (
    FormationContinueInMemoryTranslator,
)
from admission.infrastructure.admission.repository.in_memory.proposition import GlobalPropositionInMemoryRepository
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


@dataclass
class _Candidat:
    prenom: str
    nom: str
    nationalite: str


class PropositionInMemoryRepository(
    GlobalPropositionInMemoryRepository,
    InMemoryGenericRepository,
    IPropositionRepository,
):
    candidats = {
        "0123456789": _Candidat("Jean", "Dupont", "France"),
        "0000000001": _Candidat("Michel", "Durand", "Belgique"),
        "candidat": _Candidat("Pierre", "Dupond", "Belgique"),
    }
    entities: List['Proposition'] = []

    @classmethod
    def get(cls, entity_id: 'PropositionIdentity') -> 'Proposition':
        proposition = super().get(entity_id)
        if not proposition:
            raise PropositionNonTrouveeException
        return proposition

    @classmethod
    def search_dto(cls, matricule_candidat: Optional[str] = '') -> List['PropositionDTO']:
        propositions = [
            cls._load_dto(proposition)
            for proposition in cls.entities
            if proposition.matricule_candidat == matricule_candidat
        ]
        return propositions

    @classmethod
    def search(
        cls,
        entity_ids: Optional[List['PropositionIdentity']] = None,
        matricule_candidat: str = None,
        **kwargs,
    ) -> List['Proposition']:
        returned = cls.entities
        if matricule_candidat:
            returned = filter(lambda p: p.matricule_candidat == matricule_candidat, returned)
        if entity_ids:  # pragma: no cover
            returned = filter(lambda p: p.entity_id in entity_ids, returned)
        return list(returned)

    @classmethod
    def reset(cls):
        cls.entities = [
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-USCC4'),
                matricule_candidat='0123456789',
                formation_id=FormationIdentityFactory(sigle="USCC4", annee=2020),
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-USCC42'),
                matricule_candidat='0123456789',
                formation_id=FormationIdentityFactory(sigle="USCC4", annee=2020),
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-USCC43'),
                matricule_candidat='0123456789',
                formation_id=FormationIdentityFactory(sigle="USCC4", annee=2020),
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-USCC1'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="USCC1", annee=2020),
                reponses_questions_specifiques={
                    '26de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 0',
                    '26de0c3d-3c06-4c93-8eb4-c8648f04f143': 'My response 3',
                    '26de0c3d-3c06-4c93-8eb4-c8648f04f144': 'My response 4',
                    '26de0c3d-3c06-4c93-8eb4-c8648f04f145': 'My response 5',
                },
            ),
        ]

    @classmethod
    def get_dto(cls, entity_id: 'PropositionIdentity') -> 'PropositionDTO':
        return cls._load_dto(cls.get(entity_id))

    @classmethod
    def _load_dto(cls, proposition: Proposition) -> PropositionDTO:
        candidat = cls.candidats[proposition.matricule_candidat]
        formation = FormationContinueInMemoryTranslator.get_dto(
            proposition.formation_id.sigle,
            proposition.formation_id.annee,
        )

        formation_dto = FormationDTO(
            sigle=proposition.formation_id.sigle,
            annee=proposition.formation_id.annee,
            intitule=formation.intitule,
            campus=formation.campus,
            type=formation.type,
            code_domaine=formation.code_domaine,
            sigle_entite_gestion=formation.sigle_entite_gestion,
            campus_inscription=formation.campus_inscription,
        )
        return PropositionDTO(
            uuid=proposition.entity_id.uuid,
            reference=formater_reference(
                reference=proposition.reference,
                nom_campus_inscription=formation.campus_inscription,
                sigle_entite_gestion=formation.sigle_entite_gestion,
                annee=proposition.formation_id.annee,
            ),
            matricule_candidat=proposition.matricule_candidat,
            prenom_candidat=candidat.prenom,
            nom_candidat=candidat.nom,
            statut=proposition.statut.name,
            creee_le=proposition.creee_le,
            modifiee_le=proposition.modifiee_le,
            erreurs=[],
            formation=formation_dto,
            annee_calculee=proposition.annee_calculee,
            pot_calcule=proposition.pot_calcule and proposition.pot_calcule.name or '',
            soumise_le=None,
            date_fin_pot=None,
            reponses_questions_specifiques=proposition.reponses_questions_specifiques,
            equivalence_diplome=proposition.equivalence_diplome,
            curriculum=proposition.curriculum,
            inscription_a_titre=proposition.inscription_a_titre,
            nom_siege_social=proposition.nom_siege_social,
            numero_unique_entreprise=proposition.numero_unique_entreprise,
            numero_tva_entreprise=proposition.numero_tva_entreprise,
            adresse_mail_professionnelle=proposition.adresse_mail_professionnelle,
            type_adresse_facturation=proposition.type_adresse_facturation,
            adresse_facturation=proposition.adresse_facturation
            and AdressePersonnelleDTO(
                rue=proposition.adresse_facturation.rue,
                numero_rue=proposition.adresse_facturation.numero_rue,
                code_postal=proposition.adresse_facturation.code_postal,
                ville=proposition.adresse_facturation.ville,
                pays=proposition.adresse_facturation.pays,
                destinataire=proposition.adresse_facturation.destinataire,
                boite_postale=proposition.adresse_facturation.boite_postale,
                lieu_dit=proposition.adresse_facturation.lieu_dit,
            ),
        )
