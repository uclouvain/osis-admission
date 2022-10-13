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
import attr
from django.test import TestCase

from admission.ddd.admission.formation_continue.commands import SupprimerPropositionCommand
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutProposition
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition
from admission.ddd.admission.formation_continue.domain.validator.exceptions import PropositionNonTrouveeException
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class SupprimerPropositionTestCase(TestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.cmd = SupprimerPropositionCommand(
            uuid_proposition='uuid-SC3DP',
        )

    def test_should_supprimer(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(proposition.statut, ChoixStatutProposition.CANCELLED)

    def test_should_pas_supprimer_si_non_existante(self):
        cmd = attr.evolve(self.cmd, uuid_proposition="7db06048-6d86-4936-9b22-7522d11e1564")
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(cmd)
