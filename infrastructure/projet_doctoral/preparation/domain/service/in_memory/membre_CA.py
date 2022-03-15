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
from dataclasses import dataclass
from typing import List

from admission.ddd.projet_doctoral.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.projet_doctoral.preparation.domain.service.i_membre_CA import IMembreCATranslator
from admission.ddd.projet_doctoral.preparation.domain.validator.exceptions import MembreCANonTrouveException
from admission.ddd.projet_doctoral.preparation.dtos import MembreCADTO


@dataclass
class MembreCA:
    id: MembreCAIdentity
    nom: str
    prenom: str
    email: str
    externe: bool = False
    titre: str = ''
    institution: str = ''
    ville: str = ''
    pays: str = ''


class MembreCAInMemoryTranslator(IMembreCATranslator):
    membres_CA = [
        MembreCA(MembreCAIdentity('00987890'), "John", "Doe", "john.doe@example.org"),
        MembreCA(MembreCAIdentity('00987891'), "Jane", "Martin", "jane.martin@example.org"),
        MembreCA(MembreCAIdentity('00987892'), "Lucy", "Caron", "lucy.caron@example.org"),
        MembreCA(MembreCAIdentity('00987893'), "Debra", "Gibson", "debra.gibson@example.org"),
        MembreCA(MembreCAIdentity('membre-ca-SC3DP'), "John", "Doe", "john.doe@example.org"),
        MembreCA(
            MembreCAIdentity('membre-externe'),
            nom="John",
            prenom="Mills",
            email="john.mills@example.org",
            externe=True,
            titre="Dr",
            institution="USB",
            ville="Bruxelles",
            pays="Belgique",
        ),
    ]

    @classmethod
    def get(cls, matricule: str) -> 'MembreCAIdentity':
        try:
            return next(p.id for p in cls.membres_CA if p.id.matricule == matricule)
        except StopIteration:
            raise MembreCANonTrouveException

    @classmethod
    def get_dto(cls, matricule: str) -> 'MembreCADTO':
        try:
            p = next(p for p in cls.membres_CA if p.id.matricule == matricule)  # pragma: no branch
            return MembreCADTO(
                matricule=p.id.matricule,
                nom=p.nom,
                prenom=p.prenom,
                email=p.email,
                titre=p.titre,
                institution=p.institution,
                ville=p.ville,
                pays=p.pays,
            )
        except StopIteration:  # pragma: no cover
            raise MembreCANonTrouveException

    @classmethod
    def search(cls, matricules: List[str]) -> List['MembreCAIdentity']:
        raise NotImplementedError

    @classmethod
    def est_externe(cls, identity: 'MembreCAIdentity') -> bool:  # pragma: no cover
        try:
            return next(p.externe for p in cls.membres_CA if p.id.matricule == identity.matricule)
        except StopIteration:
            raise MembreCANonTrouveException
