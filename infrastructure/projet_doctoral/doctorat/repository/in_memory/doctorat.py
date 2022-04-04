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

from admission.ddd.projet_doctoral.doctorat.domain.model.doctorat import DoctoratIdentity, Doctorat
from admission.ddd.projet_doctoral.doctorat.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.domain.model.epreuve_confirmation import (
    EpreuveConfirmation,
)

from admission.ddd.projet_doctoral.doctorat.repository.i_doctorat import IDoctoratRepository
from admission.ddd.projet_doctoral.doctorat.test.factory.doctorat import (
    DoctoratSC3DPMinimaleFactory,
    DoctoratPreSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory,
    DoctoratSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory,
    DoctoratSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
)
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


class DoctoratInMemoryRepository(InMemoryGenericRepository, IDoctoratRepository):
    entities: List[EpreuveConfirmation] = list()

    @classmethod
    def get(cls, entity_id: 'DoctoratIdentity') -> 'Doctorat':
        doctorat = super().get(entity_id)
        if not doctorat:
            raise DoctoratNonTrouveException
        return doctorat

    @classmethod
    def reset(cls):
        cls.entities = [
            DoctoratSC3DPMinimaleFactory(),
            DoctoratPreSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory(),
            DoctoratSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory(),
            DoctoratSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(),
        ]
