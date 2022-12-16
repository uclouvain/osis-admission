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
from dataclasses import dataclass
from typing import List, Optional

import factory

from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.formation_continue.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_continue.dtos import PropositionDTO
from admission.ddd.admission.formation_continue.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.formation_continue.test.factory.proposition import (
    PropositionFactory,
    _PropositionIdentityFactory,
)
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository
from base.models.enums.education_group_types import TrainingType


@dataclass
class _Candidat:
    prenom: str
    nom: str
    nationalite: str


@dataclass
class _Formation:
    intitule: str
    campus: str
    type: str
    code_domaine: str


class PropositionInMemoryRepository(InMemoryGenericRepository, IPropositionRepository):
    formations = {
        ("SC3DP", 2020): _Formation(
            intitule="Doctorat en sciences",
            campus="Louvain-la-Neuve",
            type=TrainingType.PHD.name,
            code_domaine='',
        ),
        ("ECGE3DP", 2020): _Formation(
            intitule="Doctorat en sciences économiques et de gestion",
            campus="Louvain-la-Neuve",
            type=TrainingType.PHD.name,
            code_domaine='',
        ),
        ("ESP3DP", 2020): _Formation(
            intitule="Doctorat en sciences de la santé publique",
            campus="Mons",
            type=TrainingType.PHD.name,
            code_domaine='',
        ),
    }
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
    def reset(cls):
        cls.entities = [
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP'),
                matricule_candidat='0123456789',
                formation_id=FormationIdentityFactory(sigle="SC3DP", annee=2020),
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-ECGE3DP'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="ECGE3DP", annee=2020),
            ),
        ]

    @classmethod
    def get_dto(cls, entity_id: 'PropositionIdentity') -> 'PropositionDTO':
        return cls._load_dto(cls.get(entity_id))

    @classmethod
    def _load_dto(cls, proposition: Proposition) -> PropositionDTO:
        candidat = cls.candidats[proposition.matricule_candidat]
        formation = cls.formations[(proposition.formation_id.sigle, proposition.formation_id.annee)]

        return PropositionDTO(
            uuid=proposition.entity_id.uuid,
            matricule_candidat=proposition.matricule_candidat,
            prenom_candidat=candidat.prenom,
            nom_candidat=candidat.nom,
            statut=proposition.statut.name,
            creee_le=proposition.creee_le,
            modifiee_le=proposition.modifiee_le,
            erreurs=[],
            formation=FormationDTO(
                sigle=proposition.formation_id.sigle,
                annee=proposition.formation_id.annee,
                intitule=formation.intitule,
                campus=formation.campus,
                type=formation.type,
                code_domaine=formation.code_domaine,
            ),
            annee_calculee=proposition.annee_calculee,
            pot_calcule=proposition.pot_calcule,
            date_fin_pot=None,
            reponses_questions_specifiques=proposition.reponses_questions_specifiques,
            equivalence_diplome=proposition.equivalence_diplome,
            curriculum=proposition.curriculum,
        )
