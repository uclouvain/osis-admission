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
import datetime
from unittest import TestCase

from admission.ddd.parcours_doctoral.jury.commands import ModifierJuryCommand, ModifierVerificateursCommand, \
    ModifierVerificateurCommand
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.parcours_doctoral.jury.repository.in_memory.jury import JuryInMemoryRepository
from admission.infrastructure.parcours_doctoral.jury.repository.in_memory.verificateur import \
    VerificateurInMemoryRepository


class TestModifierJury(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def tearDown(self) -> None:
        VerificateurInMemoryRepository.reset()

    def test_should_modifier_verificateurs(self):
        self.message_bus.invoke(
            ModifierVerificateursCommand(
                verificateurs=[
                    ModifierVerificateurCommand(
                        entite_code='uuid-entity',
                        matricule='012345'
                    ),
                    ModifierVerificateurCommand(
                        entite_code='uuid-other-entity',
                        matricule='matricule',
                    ),
                ]
            )
        )

        self.assertEqual(len(VerificateurInMemoryRepository.entities), 2)
        verificateur = VerificateurInMemoryRepository.entities[0]
        self.assertEqual(verificateur.entity_id.code, 'uuid-entity')
        self.assertEqual(verificateur.entite_ucl_id.code, 'uuid-entity')
        self.assertEqual(verificateur.matricule, '012345')
