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
from typing import List

from admission.ddd.preparation.projet_doctoral.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.preparation.projet_doctoral.domain.service.i_membre_CA import IMembreCATranslator
from admission.ddd.preparation.projet_doctoral.dtos import MembreCADTO
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import IPersonneConnueUclTranslator


class MembreCATranslator(IMembreCATranslator):
    @classmethod
    def get(cls, matricule: str) -> 'MembreCAIdentity':
        pass

    @classmethod
    def search(cls, matricules: List[str]) -> List['MembreCAIdentity']:
        pass

    @classmethod
    def search_dto(
            cls,
            terme_de_recherche: str,
            personne_connue_ucl_translator: 'IPersonneConnueUclTranslator',
    ) -> List['MembreCADTO']:
        # TODO :: 1. signaletiques_dto = signaletique_translator.search(terme_de_recherche)
        # TODO :: 2. call cls.seacrh(matricules=signaletiques_dto)
        raise NotImplementedError
