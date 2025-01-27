# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from attr import dataclass

from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    DoctoratNonTrouveException,
)
from admission.ddd.admission.doctorat.preparation.dtos.doctorat import DoctoratDTO
from admission.ddd.admission.doctorat.preparation.repository.i_doctorat import (
    IDoctoratRepository,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixGenre
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository
from infrastructure.reference.domain.service.in_memory.bourse import (
    BourseInMemoryTranslator,
)


@dataclass
class Doctorant:
    matricule: str
    prenom: str
    nom: str
    noma: str
    genre: ChoixGenre


@dataclass
class Formation:
    intitule: str
    sigle: str
    annee: int
    campus: str


class DoctoratInMemoryRepository(InMemoryGenericRepository, IDoctoratRepository):
    dtos: List[DoctoratDTO] = list()
    doctorants = [
        Doctorant("1", "Jean", "Dupont", "01", ChoixGenre.H),
        Doctorant("2", "Michel", "Durand", "02", ChoixGenre.H),
        Doctorant("3", "Pierre", "Dupond", "03", ChoixGenre.H),
    ]

    formations = [
        Formation("Doctorat en sciences", "SC3DP", 2022, "Mons"),
        Formation("Doctorat en sciences économiques et de gestion", "ECGM3D", 2022, "Mons"),
    ]

    @classmethod
    def _get(cls, entity_id: 'DoctoratIdentity') -> 'DoctoratDTO':
        return next((dto for dto in cls.dtos if dto.uuid == entity_id.uuid), None)

    @classmethod
    def verifier_existence(cls, entity_id: 'DoctoratIdentity') -> None:
        doctorat = cls._get(entity_id)
        if not doctorat:
            raise DoctoratNonTrouveException

    @classmethod
    def get_dto(cls, entity_id: 'DoctoratIdentity') -> 'DoctoratDTO':
        doctorat = cls._get(entity_id)
        if not doctorat:
            raise DoctoratNonTrouveException

    @classmethod
    def _create_dto(cls, uuid, matricule_doctorant, reference, sigle, bourse_recherche_uuid=None):
        doctorant = next(d for d in cls.doctorants if d.matricule == matricule_doctorant)  # pragma: no branch
        formation = next(f for f in cls.formations if f.sigle == sigle)  # pragma: no branch
        bourse_recherche_dto = (
            BourseInMemoryTranslator.get_dto(uuid=str(bourse_recherche_uuid)) if bourse_recherche_uuid else None
        )

        return DoctoratDTO(
            uuid=str(uuid),
            reference=reference,
            matricule_doctorant=matricule_doctorant,
            nom_doctorant=doctorant.nom,
            prenom_doctorant=doctorant.prenom,
            annee_formation=formation.annee,
            sigle_formation=formation.sigle,
            intitule_formation=formation.intitule,
            type_admission='ADMISSION',
            titre_these='',
            type_financement='',
            bourse_recherche=bourse_recherche_dto,
            autre_bourse_recherche='',
            admission_acceptee_le=None,  # TODO to add when the field will be added to the model
            noma_doctorant=doctorant.noma,
            genre_doctorant=doctorant.genre.name,
        )

    @classmethod
    def reset(cls):
        cls.entities = [
            cls._create_dto(
                uuid='uuid-SC3DP',
                matricule_doctorant='1',
                reference='r1',
                sigle='SC3DP',
            ),
            cls._create_dto(
                uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves',
                matricule_doctorant='1',
                reference='r2',
                sigle='SC3DP',
            ),
            cls._create_dto(
                uuid='uuid-SC3DP-promoteur-refus-membre-deja-approuve',
                matricule_doctorant='2',
                reference='r3',
                sigle='SC3DP',
            ),
            cls._create_dto(
                uuid='uuid-SC3DP-promoteurs-membres-deja-approuves',
                matricule_doctorant='3',
                reference='r4',
                sigle='SC3DP',
            ),
        ]
