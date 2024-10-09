# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
    matricule: Optional[str] = None
    est_docteur: bool = False
    institution: str = ''
    ville: str = ''
    pays: str = ''
    langue: str = 'fr-be'

    @property
    def externe(self):
        return self.matricule is None


class PromoteurInMemoryTranslator(IPromoteurTranslator):
    promoteurs = [
        Promoteur(PromoteurIdentity('00987890'), "John", "Doe", "john.doe@example.org", matricule='00987890'),
        Promoteur(PromoteurIdentity('00987891'), "Jane", "Martin", "jane.martin@example.org", matricule='00987891'),
        Promoteur(PromoteurIdentity('00987892'), "Lucy", "Caron", "lucy.caron@example.org", matricule='00987892'),
        Promoteur(PromoteurIdentity('00987893'), "Debra", "Gibson", "debra.gibson@example.org", matricule='00987893'),
        Promoteur(
            PromoteurIdentity('promoteur-SC3DP-externe'),
            nom="John",
            prenom="Mills",
            email="john.mills@example.org",
            est_docteur=True,
            institution="USB",
            ville="Bruxelles",
            pays="Belgique",
        ),
        Promoteur(
            PromoteurIdentity('promoteur-SC3DP-deja-approuve'),
            nom="Jim",
            prenom="Foe",
            email="jim.foe@example.org",
            est_docteur=True,
            institution="USB",
            ville="Bruxelles",
            pays="Belgique",
        ),
        Promoteur(
            PromoteurIdentity('promoteur-SC3DP'),
            "Jeremy",
            "Sanchez",
            "jm@example.org",
            matricule='promoteur-SC3DP',
        ),
        Promoteur(
            PromoteurIdentity('promoteur-SC3DP-unique'),
            "Marcel",
            "Troufignon",
            "mt@example.org",
            matricule='promoteur-SC3DP-unique',
        ),
    ]

    @classmethod
    def get(cls, promoteur_id: 'PromoteurIdentity') -> 'PromoteurIdentity':
        raise NotImplementedError

    @classmethod
    def get_dto(cls, promoteur_id: 'PromoteurIdentity') -> 'PromoteurDTO':
        try:
            p = next(p for p in cls.promoteurs if p.id.uuid == promoteur_id.uuid)  # pragma: no branch
            return PromoteurDTO(
                uuid=p.id.uuid,
                matricule=p.matricule,
                nom=p.nom,
                prenom=p.prenom,
                email=p.email,
                est_docteur=p.est_docteur,
                institution=p.institution,
                ville=p.ville,
                pays=p.pays,
                est_externe=p.externe,
            )
        except StopIteration:  # pragma: no cover
            raise PromoteurNonTrouveException

    @classmethod
    def search(cls, matricules: List[str]) -> List['PromoteurIdentity']:
        raise NotImplementedError

    @classmethod
    def est_externe(cls, promoteur_id: 'PromoteurIdentity') -> bool:
        try:
            return next(p.externe for p in cls.promoteurs if p.id.uuid == promoteur_id.uuid)  # pragma: no branch
        except StopIteration:  # pragma: no cover
            raise PromoteurNonTrouveException

    @classmethod
    def verifier_existence(cls, matricule: Optional[str]) -> bool:
        if not matricule or any(p.id for p in cls.promoteurs if p.matricule == matricule):
            return True
        raise PromoteurNonTrouveException
