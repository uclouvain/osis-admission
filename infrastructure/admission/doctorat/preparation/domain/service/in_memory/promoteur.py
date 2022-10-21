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

from admission.ddd.admission.doctorat.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import PromoteurNonTrouveException
from admission.ddd.admission.doctorat.preparation.dtos import PromoteurDTO
from admission.infrastructure.admission.doctorat.preparation.domain.service.promoteur import IPromoteurTranslator


@dataclass
class Promoteur:
    id: PromoteurIdentity
    nom: str
    prenom: str
    email: str
    externe: bool = False
    titre: str = ''
    institution: str = ''
    ville: str = ''
    pays: str = ''


class PromoteurInMemoryTranslator(IPromoteurTranslator):
    promoteurs = [
        Promoteur(PromoteurIdentity('00987890'), "John", "Doe", "john.doe@example.org"),
        Promoteur(PromoteurIdentity('00987891'), "Jane", "Martin", "jane.martin@example.org"),
        Promoteur(PromoteurIdentity('00987892'), "Lucy", "Caron", "lucy.caron@example.org"),
        Promoteur(PromoteurIdentity('00987893'), "Debra", "Gibson", "debra.gibson@example.org"),
        Promoteur(
            PromoteurIdentity('promoteur-SC3DP-externe'),
            nom="John",
            prenom="Mills",
            email="john.mills@example.org",
            externe=True,
            titre="Dr",
            institution="USB",
            ville="Bruxelles",
            pays="Belgique",
        ),
        Promoteur(PromoteurIdentity('promoteur-SC3DP'), "Jeremy", "Sanchez", "jm@example.org"),
        Promoteur(PromoteurIdentity('promoteur-SC3DP-unique'), "Marcel", "Troufignon", "mt@example.org"),
    ]

    @classmethod
    def get(cls, matricule: str) -> 'PromoteurIdentity':
        try:
            return next(p.id for p in cls.promoteurs if p.id.matricule == matricule)
        except StopIteration:
            raise PromoteurNonTrouveException

    @classmethod
    def get_dto(cls, matricule: str) -> 'PromoteurDTO':
        try:
            p = next(p for p in cls.promoteurs if p.id.matricule == matricule)  # pragma: no branch
            return PromoteurDTO(
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
            raise PromoteurNonTrouveException

    @classmethod
    def search(cls, matricules: List[str]) -> List['PromoteurIdentity']:
        raise NotImplementedError

    @classmethod
    def est_externe(cls, identity: 'PromoteurIdentity') -> bool:
        try:
            return next(p.externe for p in cls.promoteurs if p.id.matricule == identity.matricule)  # pragma: no branch
        except StopIteration:  # pragma: no cover
            raise PromoteurNonTrouveException
