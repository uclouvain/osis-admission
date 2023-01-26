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

from admission.ddd import CODE_BACHELIER_VETERINAIRE
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.formation_generale.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_generale.dtos import PropositionDTO
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.formation_generale.test.factory.proposition import (
    PropositionFactory,
    _PropositionIdentityFactory,
)
from admission.ddd.admission.repository.i_proposition import formater_reference
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.domain.service.in_memory.bourse import BourseInMemoryTranslator
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.formation import (
    FormationGeneraleInMemoryTranslator,
)
from admission.infrastructure.admission.repository.in_memory.proposition import GlobalPropositionInMemoryRepository
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


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


class PropositionInMemoryRepository(
    GlobalPropositionInMemoryRepository,
    InMemoryGenericRepository,
    IPropositionRepository,
):
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
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-MASTER-SCI'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="MASTER-SCI", annee=2020),
                bourse_double_diplome_id=BourseInMemoryTranslator.bourse_dd_1.entity_id,
                bourse_erasmus_mundus_id=BourseInMemoryTranslator.bourse_em_1.entity_id,
                bourse_internationale_id=BourseInMemoryTranslator.bourse_ifg_1.entity_id,
                curriculum=['file1.pdf'],
                continuation_cycle_bachelier=['file1.pdf'],
                attestation_continuation_cycle_bachelier=None,
                reponses_questions_specifiques={
                    '16de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 0',
                    '16de0c3d-3c06-4c93-8eb4-c8648f04f141': 'My response 1',
                    '16de0c3d-3c06-4c93-8eb4-c8648f04f142': 'My response 2',
                    '16de0c3d-3c06-4c93-8eb4-c8648f04f143': 'My response 3',
                    '16de0c3d-3c06-4c93-8eb4-c8648f04f144': 'My response 4',
                },
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-BACHELIER-ECO1'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="BACHELIER-ECO", annee=2020),
                continuation_cycle_bachelier=['file1.pdf'],
                attestation_continuation_cycle_bachelier=None,
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-BACHELIER-VET'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle=CODE_BACHELIER_VETERINAIRE, annee=2020),
                continuation_cycle_bachelier=['file1.pdf'],
                attestation_continuation_cycle_bachelier=True,
                est_non_resident_au_sens_decret=False,
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-AGGREGATION-ECO'),
                matricule_candidat='0000000002',
                formation_id=FormationIdentityFactory(sigle="AGGREGATION-ECO", annee=2020),
                curriculum=['file1.pdf'],
                equivalence_diplome=['file1.pdf'],
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-CAPAES-ECO'),
                matricule_candidat='0000000002',
                formation_id=FormationIdentityFactory(sigle="CAPAES-ECO", annee=2020),
                curriculum=['file1.pdf'],
                equivalence_diplome=['file1.pdf'],
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-BACHELIER-ECO2'),
                matricule_candidat='0123456789',
                formation_id=FormationIdentityFactory(sigle="BACHELIER-ECO", annee=2020),
                bourse_erasmus_mundus_id=BourseInMemoryTranslator.bourse_em_1.entity_id,
                continuation_cycle_bachelier=False,
            ),
        ]

    @classmethod
    def get_dto(cls, entity_id: 'PropositionIdentity') -> 'PropositionDTO':
        return cls._load_dto(cls.get(entity_id))

    @classmethod
    def _load_dto(cls, proposition: Proposition) -> PropositionDTO:
        candidat = ProfilCandidatInMemoryTranslator.get_identification(proposition.matricule_candidat)
        formation = FormationGeneraleInMemoryTranslator.get_dto(
            proposition.formation_id.sigle,
            proposition.formation_id.annee,
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
            creee_le=proposition.creee_le,
            modifiee_le=proposition.modifiee_le,
            statut=proposition.statut.name,
            erreurs=[],
            formation=formation,
            annee_calculee=proposition.annee_calculee,
            pot_calcule=proposition.pot_calcule and proposition.pot_calcule.name or '',
            date_fin_pot=None,
            bourse_double_diplome=BourseInMemoryTranslator.get_dto(proposition.bourse_double_diplome_id.uuid)
            if proposition.bourse_double_diplome_id
            else None,
            bourse_erasmus_mundus=BourseInMemoryTranslator.get_dto(proposition.bourse_erasmus_mundus_id.uuid)
            if proposition.bourse_erasmus_mundus_id
            else None,
            bourse_internationale=BourseInMemoryTranslator.get_dto(proposition.bourse_internationale_id.uuid)
            if proposition.bourse_internationale_id
            else None,
            reponses_questions_specifiques=proposition.reponses_questions_specifiques,
            continuation_cycle_bachelier=proposition.continuation_cycle_bachelier,
            attestation_continuation_cycle_bachelier=proposition.attestation_continuation_cycle_bachelier,
            equivalence_diplome=proposition.equivalence_diplome,
            curriculum=proposition.curriculum,
        )
