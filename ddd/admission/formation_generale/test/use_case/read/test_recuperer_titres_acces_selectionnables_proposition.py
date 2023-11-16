# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict

from django.test import SimpleTestCase

from admission.ddd.admission.dtos.titre_acces_selectionnable import TitreAccesSelectionnableDTO
from admission.ddd.admission.formation_generale.commands import (
    RecupererTitresAccesSelectionnablesPropositionQuery,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.titre_acces_selectionnable import (
    TitreAccesSelectionnableInMemoryRepositoryFactory,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestRecupererTitresAccesSelectionnablesProposition(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.titre_acces_repository = TitreAccesSelectionnableInMemoryRepositoryFactory()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance

    def test_should_recuperer_titres_acces_selectionnables_proposition(self):
        titres: Dict[str, TitreAccesSelectionnableDTO] = self.message_bus.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
            )
        )

        self.assertEqual(len(titres), 1)

        entite = self.titre_acces_repository.entities[0]

        self.assertIn(entite.entity_id.uuid_experience, titres)

        self.assertEqual(titres[entite.entity_id.uuid_experience].type_titre, entite.entity_id.type_titre.name)
        self.assertEqual(titres[entite.entity_id.uuid_experience].uuid_experience, entite.entity_id.uuid_experience)
        self.assertEqual(titres[entite.entity_id.uuid_experience].annee, entite.annee)
        self.assertEqual(titres[entite.entity_id.uuid_experience].selectionne, entite.selectionne)
