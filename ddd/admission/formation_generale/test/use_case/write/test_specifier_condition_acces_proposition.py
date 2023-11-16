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

from django.test import SimpleTestCase

from admission.ddd.admission.formation_generale.commands import SpecifierConditionAccesPropositionCommand
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PropositionNonTrouveeException,
)
from admission.ddd.admission.formation_generale.test.factory.titre_acces import TitreAccesSelectionnableFactory
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.titre_acces_selectionnable import (
    TitreAccesSelectionnableInMemoryRepositoryFactory,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from epc.models.enums.condition_acces import ConditionAcces


class TestSpecifierConditionAccesPropositionService(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.titre_acces_repository = TitreAccesSelectionnableInMemoryRepositoryFactory()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance

    def test_should_specifier_condition_acces_et_millesime_proposition(self):
        proposition_id = self.message_bus.invoke(
            SpecifierConditionAccesPropositionCommand(
                uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                condition_acces=ConditionAcces.BAC.name,
                millesime_condition_acces=2021,
            )
        )
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.condition_acces, ConditionAcces.BAC)
        self.assertEqual(proposition.millesime_condition_acces, 2021)

    def test_should_remplir_automatiquement_millesime_si_un_titre_acces_selectionne(self):
        self.titre_acces_repository.entities.append(
            TitreAccesSelectionnableFactory(
                entity_id__uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                selectionne=True,
                annee=2022,
            )
        )

        proposition_id = self.message_bus.invoke(
            SpecifierConditionAccesPropositionCommand(
                uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                condition_acces=ConditionAcces.BAC.name,
                millesime_condition_acces=2021,
            )
        )

        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.condition_acces, ConditionAcces.BAC)
        self.assertEqual(proposition.millesime_condition_acces, 2022)

    def test_should_pas_remplir_automatiquement_millesime_deux_titres_acces_selectionnes(self):
        self.titre_acces_repository.entities.append(
            TitreAccesSelectionnableFactory(
                entity_id__uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                selectionne=True,
                annee=2022,
            )
        )

        self.titre_acces_repository.entities.append(
            TitreAccesSelectionnableFactory(
                entity_id__uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                selectionne=True,
                annee=2023,
            )
        )

        proposition_id = self.message_bus.invoke(
            SpecifierConditionAccesPropositionCommand(
                uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                condition_acces=ConditionAcces.BAC.name,
                millesime_condition_acces=2021,
            )
        )

        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.condition_acces, ConditionAcces.BAC)
        self.assertEqual(proposition.millesime_condition_acces, 2021)

    def test_should_empecher_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                SpecifierConditionAccesPropositionCommand(
                    uuid_proposition='INCONNUE',
                )
            )
