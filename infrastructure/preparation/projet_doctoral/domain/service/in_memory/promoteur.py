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
import contextlib
from typing import List

from admission.ddd.preparation.projet_doctoral.domain.model._promoteur import PromoteurIdentity
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import PromoteurNonTrouveException
from admission.ddd.preparation.projet_doctoral.dtos import PromoteurDTO
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import IPersonneConnueUclTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.promoteur import IPromoteurTranslator


class PromoteurInMemoryTranslator(IPromoteurTranslator):
    promoteurs = [
        PromoteurIdentity('00987890')
    ]

    @classmethod
    def get(cls, matricule: str) -> 'PromoteurIdentity':
        try:
            return next(p for p in cls.promoteurs if p.matricule == matricule)
        except StopIteration:
            raise PromoteurNonTrouveException

    @classmethod
    def search(cls, matricules: List[str]) -> List['PromoteurIdentity']:
        return [p for p in cls.promoteurs if p.matricule in matricules]

    @classmethod
    def search_dto(
            cls,
            terme_de_recherche: str,
            personne_connue_ucl_translator: 'IPersonneConnueUclTranslator',
    ) -> List['PromoteurDTO']:
        results = []
        personnes = personne_connue_ucl_translator.search(terme_de_recherche)
        for personne in personnes:
            with contextlib.suppress:
                promoteur = cls.get(personne.matricule)
                results.append(PromoteurDTO(
                    matricule=promoteur.matricule,
                    prenom=personne.prenom,
                    nom=personne.nom,
                ))
        return results
