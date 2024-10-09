# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.test import SimpleTestCase

from admission.ddd.admission.domain.model.enums.condition_acces import TypeTitreAccesSelectionnable
from admission.ddd.admission.formation_generale.commands import (
    SpecifierExperienceEnTantQueTitreAccesCommand,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.titre_acces_selectionnable import (
    TitreAccesSelectionnableInMemoryRepositoryFactory,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestSpecifierExperienceEnTantQueTitreAcces(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.titre_acces_repository = TitreAccesSelectionnableInMemoryRepositoryFactory()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance

    def test_should_specifier_experience_en_tant_que_titre_acces(self):
        titre_acces_id = self.message_bus.invoke(
            SpecifierExperienceEnTantQueTitreAccesCommand(
                uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                uuid_experience='uuid-EXP-1',
                type_experience=TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE.name,
                selectionne=True,
            )
        )
        titre_acces = self.titre_acces_repository.get(titre_acces_id)

        self.assertEqual(titre_acces.selectionne, True)
        self.assertEqual(titre_acces.annee, None)
        self.assertEqual(titre_acces.entity_id.type_titre, TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE)
        self.assertEqual(titre_acces.entity_id.uuid_experience, 'uuid-EXP-1')
        self.assertEqual(titre_acces.entity_id.uuid_proposition, 'uuid-MASTER-SCI-CONFIRMED')
