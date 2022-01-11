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

from admission.auth.roles.promoter import Promoter
from admission.ddd.preparation.projet_doctoral.domain.model._promoteur import PromoteurIdentity
from admission.ddd.preparation.projet_doctoral.domain.service.i_promoteur import IPromoteurTranslator
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import PromoteurNonTrouveException
from admission.ddd.preparation.projet_doctoral.dtos import PromoteurDTO
from base.auth.roles.tutor import Tutor
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import IPersonneConnueUclTranslator


class PromoteurTranslator(IPromoteurTranslator):
    @classmethod
    def get(cls, matricule: str) -> 'PromoteurIdentity':
        if not Tutor.objects.filter(person__global_id=matricule):
            raise PromoteurNonTrouveException
        return PromoteurIdentity(matricule=matricule)

    @classmethod
    def search(cls, matricules: List[str]) -> List['PromoteurIdentity']:
        raise NotImplementedError

    @classmethod
    def search_dto(
            cls,
            terme_de_recherche: str,
            personne_connue_ucl_translator: 'IPersonneConnueUclTranslator',
    ) -> List['PromoteurDTO']:
        # TODO :: 1. signaletiques_dto = signaletique_translator.search(terme_de_recherche)
        # TODO :: 2. call cls.seacrh(matricules=signaletiques_dto)
        raise NotImplementedError

    @classmethod
    def est_externe(cls, identity: 'PromoteurIdentity') -> bool:
        return Promoter.objects.get(person__global_id=identity.matricule).is_external
