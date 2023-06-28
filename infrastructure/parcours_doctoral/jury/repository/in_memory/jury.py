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
from admission.ddd.parcours_doctoral.jury.dtos.jury import JuryDTO, MembreJuryDTO
from admission.ddd.parcours_doctoral.jury.repository.i_jury import IJuryRepository
from admission.ddd.parcours_doctoral.jury.test.factory.jury import JuryFactory, MembreJuryFactory
from admission.ddd.parcours_doctoral.jury.validator.exceptions import (
    JuryNonTrouveException,
    MembreNonTrouveDansJuryException,
)
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


class JuryInMemoryRepository(InMemoryGenericRepository, IJuryRepository):
    entities: List[Jury] = list()

    @classmethod
    def reset(cls):
        cls.entities = [
            JuryFactory(
                entity_id__uuid='uuid-jury',
                membres=[
                    MembreJuryFactory(uuid='uuid-membre'),
                    MembreJuryFactory(uuid='uuid-promoteur', est_promoteur=True),
                ],
            ),
        ]

    @classmethod
    def save(cls, entity: 'Jury') -> 'JuryIdentity':
        try:
            jury = cls.get(entity.entity_id)
            if entity.membres is None and jury.membres is not None:
                entity.membres = jury.membres
            cls.entities.remove(jury)
        except JuryNonTrouveException:
            entity.id = len(cls.entities)
        cls.entities.append(entity)

        return entity.entity_id

    @classmethod
    def get(cls, entity_id: 'JuryIdentity') -> 'Jury':
        jury = super().get(entity_id)
        if not jury:
            raise JuryNonTrouveException
        return jury

    @classmethod
    def get_dto(cls, entity_id) -> JuryDTO:
        jury = cls.get(entity_id=entity_id)
        return cls._load_jury_dto(jury)

    @classmethod
    def get_membre_dto(cls, entity_id, membre_uuid) -> MembreJuryDTO:
        jury = cls.get_dto(entity_id)
        for membre in jury.membres:
            if str(membre.uuid) == membre_uuid:
                return membre
        raise MembreNonTrouveDansJuryException(jury=jury, uuid_membre=membre_uuid)

    @classmethod
    def _load_jury_dto(cls, jury: Jury) -> JuryDTO:
        return JuryDTO(
            uuid=jury.entity_id.uuid,
            titre_propose=jury.titre_propose,
            cotutelle=jury.cotutelle,
            institution_cotutelle=jury.institution_cotutelle,
            membres=[
                MembreJuryDTO(
                    uuid=membre.uuid,
                    role=str(membre.role),
                    est_promoteur=membre.est_promoteur,
                    matricule=membre.matricule,
                    institution=str(membre.institution),
                    autre_institution=str(membre.autre_institution),
                    pays=membre.pays,
                    nom=membre.nom,
                    prenom=membre.prenom,
                    titre=str(membre.titre),
                    justification_non_docteur=membre.justification_non_docteur,
                    genre=str(membre.genre),
                    email=membre.email,
                )
                for membre in jury.membres
            ],
            formule_defense=jury.formule_defense,
            date_indicative=jury.date_indicative,
            langue_redaction=jury.langue_redaction,
            langue_soutenance=jury.langue_soutenance,
            commentaire=jury.commentaire,
            situation_comptable=jury.situation_comptable,
            approbation_pdf=jury.approbation_pdf,
        )
