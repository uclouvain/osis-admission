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
from typing import List
from unittest import TestCase

from admission.ddd.parcours_doctoral.jury.commands import RecupererJuryQuery, RecupererVerificateursQuery
from admission.ddd.parcours_doctoral.jury.dtos.jury import JuryDTO
from admission.ddd.parcours_doctoral.jury.dtos.verificateur import VerificateurDTO
from admission.ddd.parcours_doctoral.jury.validator.exceptions import JuryNonTrouveException
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.parcours_doctoral.jury.repository.in_memory.verificateur import \
    VerificateurInMemoryRepository


class TestRecupererJury(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def tearDown(self) -> None:
        VerificateurInMemoryRepository.reset()

    def test_should_recuperer_verificateurs(self):
        verificateurs: List[VerificateurDTO] = self.message_bus.invoke(
            RecupererVerificateursQuery()
        )
        self.assertEqual(len(verificateurs), 2)
        verificateur = verificateurs[0]
        self.assertEqual(verificateur.uuid, 'uuid-verificateur')
        self.assertEqual(verificateur.entite_ucl_id, 'uuid-entity')
        self.assertIsNone(verificateur.matricule)
        verificateur = verificateurs[1]
        self.assertEqual(verificateur.uuid, 'uuid-verificateur2')
        self.assertEqual(verificateur.entite_ucl_id, 'uuid-other-entity')
        self.assertEqual(verificateur.matricule, 'matricule')
