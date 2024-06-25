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
from typing import List, Optional

from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.model.titre_acces_selectionnable import (
    TitreAccesSelectionnable,
)
from admission.ddd.admission.domain.repository.i_titre_acces_selectionnable import ITitreAccesSelectionnableRepository
from admission.ddd.admission.formation_generale.test.factory.titre_acces import TitreAccesSelectionnableFactory
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository
from ddd.logic.shared_kernel.profil.domain.service.parcours_interne import IExperienceParcoursInterneTranslator


class TitreAccesSelectionnableInMemoryRepository(InMemoryGenericRepository, ITitreAccesSelectionnableRepository):
    entities: List[TitreAccesSelectionnable]

    @classmethod
    def search_by_proposition(
        cls,
        proposition_identity: PropositionIdentity,
        experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
        seulement_selectionnes: Optional[bool] = None,
    ) -> List[TitreAccesSelectionnable]:
        return [
            entity
            for entity in cls.entities
            if entity.entity_id.uuid_proposition == proposition_identity.uuid
            and (not seulement_selectionnes or entity.selectionne)
        ]


class TitreAccesSelectionnableInMemoryRepositoryFactory(TitreAccesSelectionnableInMemoryRepository):
    def __init__(self):
        TitreAccesSelectionnableInMemoryRepositoryFactory.entities = [
            TitreAccesSelectionnableFactory(entity_id__uuid_proposition='uuid-MASTER-SCI-CONFIRMED', annee=2020),
        ]
