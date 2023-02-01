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

from attr import dataclass

from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixGenre
from admission.ddd.parcours_doctoral.domain.model.doctorat import Doctorat, DoctoratIdentity
from admission.ddd.parcours_doctoral.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.parcours_doctoral.dtos import DoctoratDTO
from admission.ddd.parcours_doctoral.epreuve_confirmation.domain.model.epreuve_confirmation import (
    EpreuveConfirmation,
)
from admission.ddd.parcours_doctoral.repository.i_doctorat import IDoctoratRepository
from admission.ddd.parcours_doctoral.test.factory.doctorat import (
    DoctoratPreSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory,
    DoctoratSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory,
    DoctoratSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    DoctoratSC3DPMinimaleFactory,
)
from admission.infrastructure.admission.domain.service.in_memory.bourse import BourseInMemoryTranslator
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


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


class DoctoratInMemoryRepository(InMemoryGenericRepository, IDoctoratRepository):
    entities: List[EpreuveConfirmation] = list()
    doctorants = [
        Doctorant("1", "Jean", "Dupont", "01", ChoixGenre.H),
        Doctorant("2", "Michel", "Durand", "02", ChoixGenre.H),
        Doctorant("3", "Pierre", "Dupond", "03", ChoixGenre.H),
    ]

    formations = [
        Formation("Doctorat en sciences", "SC3DP", 2022),
        Formation("Doctorat en sciences économiques et de gestion", "ECGM3D", 2022),
    ]

    @classmethod
    def get(cls, entity_id: 'DoctoratIdentity') -> 'Doctorat':
        doctorat = super().get(entity_id)
        if not doctorat:
            raise DoctoratNonTrouveException
        return doctorat

    @classmethod
    def verifier_existence(cls, entity_id: 'DoctoratIdentity') -> None:
        doctorat = super().get(entity_id)
        if not doctorat:
            raise DoctoratNonTrouveException

    @classmethod
    def get_dto(cls, entity_id: 'DoctoratIdentity') -> 'DoctoratDTO':
        doctorat = cls.get(entity_id)
        doctorant = next(d for d in cls.doctorants if d.matricule == doctorat.matricule_doctorant)  # pragma: no branch
        formation = next(f for f in cls.formations if f.sigle == doctorat.formation_id.sigle)  # pragma: no branch
        bourse_recherche_dto = (
            BourseInMemoryTranslator.get_dto(uuid=str(doctorat.bourse_recherche.uuid))
            if doctorat.bourse_recherche
            else None
        )

        return DoctoratDTO(
            uuid=str(entity_id.uuid),
            statut=doctorat.statut.name,
            reference=doctorat.reference,
            matricule_doctorant=doctorat.matricule_doctorant,
            nom_doctorant=doctorant.nom,
            prenom_doctorant=doctorant.prenom,
            annee_formation=formation.annee,
            sigle_formation=formation.sigle,
            intitule_formation=formation.intitule,
            type_admission='ADMISSION',
            titre_these='',
            type_financement='',
            bourse_recherche=bourse_recherche_dto,
            autre_bourse_recherche=doctorat.autre_bourse_recherche,
            admission_acceptee_le=None,  # TODO to add when the field will be added to the model
            noma_doctorant=doctorant.noma,
            genre_doctorant=doctorant.genre.name,
        )

    @classmethod
    def reset(cls):
        cls.entities = [
            DoctoratSC3DPMinimaleFactory(),
            DoctoratPreSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory(),
            DoctoratSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory(),
            DoctoratSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(),
        ]
