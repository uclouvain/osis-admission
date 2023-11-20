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
from typing import List

from admission.ddd.parcours_doctoral.domain.model.doctorat import DoctoratIdentity
from admission.ddd.parcours_doctoral.epreuve_confirmation.domain.model.epreuve_confirmation import (
    EpreuveConfirmation,
    EpreuveConfirmationIdentity,
)
from admission.ddd.parcours_doctoral.epreuve_confirmation.dtos import DemandeProlongationDTO, EpreuveConfirmationDTO
from admission.ddd.parcours_doctoral.epreuve_confirmation.repository.i_epreuve_confirmation import (
    IEpreuveConfirmationRepository,
)
from admission.ddd.parcours_doctoral.epreuve_confirmation.test.factory.epreuve_confirmation import (
    EpreuveConfirmation0DoctoratSC3DPFactory,
    EpreuveConfirmation1DoctoratSC3DPFactory,
    EpreuveConfirmation2DoctoratSC3DPFactory,
)
from admission.ddd.parcours_doctoral.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonTrouveeException,
)
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


class EpreuveConfirmationInMemoryRepository(InMemoryGenericRepository, IEpreuveConfirmationRepository):
    entities: List[EpreuveConfirmation] = list()
    dtos: List[EpreuveConfirmationDTO] = list()

    @classmethod
    def search_by_doctorat_identity(cls, doctorat_entity_id: 'DoctoratIdentity') -> List['EpreuveConfirmation']:
        result = [entity for entity in cls.entities if entity.doctorat_id.uuid == doctorat_entity_id.uuid]
        result.sort(key=lambda x: x.id, reverse=True)
        return result

    @classmethod
    def search_dto_by_doctorat_identity(cls, doctorat_entity_id: 'DoctoratIdentity') -> List['EpreuveConfirmationDTO']:
        result = cls.search_by_doctorat_identity(doctorat_entity_id)
        return [cls._load_confirmation_dto(entity) for entity in result]

    @classmethod
    def get_dto_by_doctorat_identity(cls, doctorat_entity_id: 'DoctoratIdentity') -> 'EpreuveConfirmationDTO':
        first_result = cls.search_by_doctorat_identity(doctorat_entity_id)
        if not first_result:
            raise EpreuveConfirmationNonTrouveeException
        return cls._load_confirmation_dto(first_result[0])

    @classmethod
    def reset(cls):
        cls.entities = [
            EpreuveConfirmation0DoctoratSC3DPFactory(id=0),
            EpreuveConfirmation2DoctoratSC3DPFactory(id=1),
            EpreuveConfirmation1DoctoratSC3DPFactory(id=2),
        ]

    @classmethod
    def save(cls, entity: 'EpreuveConfirmation') -> 'EpreuveConfirmationIdentity':
        try:
            epreuve_confirmation = cls.get(entity.entity_id)
            cls.entities.remove(epreuve_confirmation)
        except EpreuveConfirmationNonTrouveeException:
            entity.id = len(cls.entities)
        cls.entities.append(entity)

        return entity.entity_id

    @classmethod
    def get(cls, entity_id: 'EpreuveConfirmationIdentity') -> 'EpreuveConfirmation':
        epreuve_confirmation = super().get(entity_id)
        if not epreuve_confirmation:
            raise EpreuveConfirmationNonTrouveeException
        return epreuve_confirmation

    @classmethod
    def get_dto(cls, entity_id) -> EpreuveConfirmationDTO:
        epreuve_confirmation = cls.get(entity_id=entity_id)
        return cls._load_confirmation_dto(epreuve_confirmation)

    @classmethod
    def _load_confirmation_dto(cls, confirmation_paper: EpreuveConfirmation) -> EpreuveConfirmationDTO:
        return EpreuveConfirmationDTO(
            uuid=str(confirmation_paper.entity_id.uuid),
            date_limite=confirmation_paper.date_limite,
            date=confirmation_paper.date,
            rapport_recherche=confirmation_paper.rapport_recherche,
            demande_prolongation=DemandeProlongationDTO(
                nouvelle_echeance=confirmation_paper.demande_prolongation.nouvelle_echeance,
                justification_succincte=confirmation_paper.demande_prolongation.justification_succincte,
                lettre_justification=confirmation_paper.demande_prolongation.lettre_justification,
                avis_cdd=confirmation_paper.demande_prolongation.avis_cdd,
            )
            if confirmation_paper.demande_prolongation
            else None,
            proces_verbal_ca=confirmation_paper.proces_verbal_ca,
            attestation_reussite=confirmation_paper.attestation_reussite,
            attestation_echec=confirmation_paper.attestation_echec,
            canevas_proces_verbal_ca=confirmation_paper.canevas_proces_verbal_ca,
            avis_renouvellement_mandat_recherche=confirmation_paper.avis_renouvellement_mandat_recherche,
        )
