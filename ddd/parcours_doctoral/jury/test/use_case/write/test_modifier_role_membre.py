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
from unittest import TestCase

from admission.ddd.parcours_doctoral.jury.commands import ModifierRoleMembreCommand
from admission.ddd.parcours_doctoral.jury.domain.model.enums import RoleJury
from admission.ddd.parcours_doctoral.jury.test.factory.jury import MembreJuryFactory
from admission.ddd.parcours_doctoral.jury.validator.exceptions import (
    MembreNonTrouveDansJuryException,
    JuryNonTrouveException,
    PromoteurPresidentException,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.parcours_doctoral.jury.repository.in_memory.jury import JuryInMemoryRepository
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestModifierRoleMembre(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def tearDown(self) -> None:
        JuryInMemoryRepository.reset()

    def test_should_modifier_role_membre(self):
        self.message_bus.invoke(
            ModifierRoleMembreCommand(
                uuid_jury='uuid-jury',
                uuid_membre='uuid-membre',
                role='PRESIDENT',
            )
        )

        jury = JuryInMemoryRepository.entities[0]
        self.assertEqual(len(jury.membres), 2)
        membre = jury.membres[-1]
        self.assertEqual(membre.role, RoleJury.PRESIDENT.name)

    def test_should_pas_trouve_si_modifier_role_membre_inexistant(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                ModifierRoleMembreCommand(
                    uuid_jury='uuid-jury',
                    uuid_membre='uuid-membre-inexistant',
                    role='PRESIDENT',
                )
            )
            self.assertIsInstance(context.exception.exceptions.pop(), MembreNonTrouveDansJuryException)

    def test_should_pas_trouve_si_modifier_role_membre_jury_inexistant(self):
        with self.assertRaises(JuryNonTrouveException):
            self.message_bus.invoke(
                ModifierRoleMembreCommand(
                    uuid_jury='uuid-jury-inexistant',
                    uuid_membre='uuid-membre',
                    role='PRESIDENT',
                )
            )

    def test_should_modifier_role_promoteur(self):
        self.message_bus.invoke(
            ModifierRoleMembreCommand(
                uuid_jury='uuid-jury',
                uuid_membre='uuid-promoteur',
                role='SECRETAIRE',
            )
        )

        jury = JuryInMemoryRepository.entities[0]
        self.assertEqual(len(jury.membres), 2)
        promoteur = jury.membres[-1]
        self.assertEqual(promoteur.role, RoleJury.SECRETAIRE.name)

    def test_should_exception_si_modifier_role_promoteur_president(self):
        with self.assertRaises(PromoteurPresidentException):
            self.message_bus.invoke(
                ModifierRoleMembreCommand(
                    uuid_jury='uuid-jury',
                    uuid_membre='uuid-promoteur',
                    role='PRESIDENT',
                )
            )

    def test_should_modifier_role_membre_autre_membre_president(self):
        JuryInMemoryRepository.entities[0].membres.append(
            MembreJuryFactory(uuid='uuid-president', role=RoleJury.PRESIDENT.name)
        )

        self.message_bus.invoke(
            ModifierRoleMembreCommand(
                uuid_jury='uuid-jury',
                uuid_membre='uuid-membre',
                role='PRESIDENT',
            )
        )

        jury = JuryInMemoryRepository.entities[0]
        self.assertEqual(len(jury.membres), 3)
        for membre in jury.membres:
            if membre.uuid == 'uuid-president':
                self.assertEqual(membre.role, RoleJury.MEMBRE.name)
            elif membre.uuid == 'uuid-membre':
                self.assertEqual(membre.role, RoleJury.PRESIDENT.name)
