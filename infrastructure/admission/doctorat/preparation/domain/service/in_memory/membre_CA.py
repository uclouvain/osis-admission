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

from admission.ddd.admission.doctorat.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_membre_CA import IMembreCATranslator
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import MembreCANonTrouveException
from admission.ddd.admission.doctorat.preparation.dtos import MembreCADTO


@dataclass
class MembreCA:
    id: MembreCAIdentity
    nom: str
    prenom: str
    email: str
    matricule: Optional[str] = None
    est_docteur: bool = False
    institution: str = ''
    ville: str = ''
    pays: str = ''
    langue: str = 'fr-be'
    est_membre_reference: bool = False


class MembreCAInMemoryTranslator(IMembreCATranslator):
    membres_CA = [
        MembreCA(MembreCAIdentity('00987890'), "John", "Doe", "john.doe@example.org", matricule='00987890'),
        MembreCA(MembreCAIdentity('00987891'), "Jane", "Martin", "jane.martin@example.org", matricule='00987891'),
        MembreCA(MembreCAIdentity('00987892'), "Lucy", "Caron", "lucy.caron@example.org", matricule='00987892'),
        MembreCA(MembreCAIdentity('00987893'), "Debra", "Gibson", "debra.gibson@example.org", matricule='00987893'),
        MembreCA(
            MembreCAIdentity('membre-ca-SC3DP'), "John", "Doe", "john.doe@example.org", matricule='membre-ca-SC3DP'
        ),
        MembreCA(
            MembreCAIdentity('membre-ca-SC3DP2'), "John", "Doe", "john.doe2@example.org", matricule='membre-ca-SC3DP2'
        ),
        MembreCA(
            MembreCAIdentity('membre-externe'),
            nom="John",
            prenom="Mills",
            email="john.mills@example.org",
            est_docteur=True,
            institution="USB",
            ville="Bruxelles",
            pays="Belgique",
        ),
    ]

    @classmethod
    def get(cls, membre_ca_id: str) -> 'MembreCAIdentity':
        raise NotImplementedError

    @classmethod
    def get_dto(cls, membre_ca_id: 'MembreCAIdentity') -> 'MembreCADTO':
        try:
            p = next(p for p in cls.membres_CA if p.id == membre_ca_id)  # pragma: no branch
            return MembreCADTO(
                uuid=p.id.uuid,
                matricule=p.matricule,
                nom=p.nom,
                prenom=p.prenom,
                email=p.email,
                est_docteur=p.est_docteur,
                institution=p.institution,
                ville=p.ville,
                pays=p.pays,
                langue=p.langue,
                est_membre_reference=p.est_membre_reference,
            )
        except StopIteration:  # pragma: no cover
            raise MembreCANonTrouveException

    @classmethod
    def search(cls, matricules: List[str]) -> List['MembreCAIdentity']:
        raise NotImplementedError

    @classmethod
    def est_externe(cls, membre_ca_id: 'MembreCAIdentity') -> bool:
        raise NotImplementedError

    @classmethod
    def verifier_existence(cls, matricule: str) -> bool:
        if not matricule or any(p.id for p in cls.membres_CA if p.matricule == matricule):
            return True
        raise MembreCANonTrouveException
