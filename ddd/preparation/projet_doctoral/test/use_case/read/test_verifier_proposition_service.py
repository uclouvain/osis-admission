# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
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

from admission.ddd.preparation.projet_doctoral.commands import VerifierPropositionCommand
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (IdentificationNonCompleteeException)
from admission.ddd.preparation.projet_doctoral.test.factory.proposition import PropositionAdmissionSC3DPMinimaleFactory
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.preparation.projet_doctoral.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.preparation.projet_doctoral.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.tests import TestCase
from admission.tests.factories.roles import CandidateFactory
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestVerifierPropositionService(TestCase):
    def setUp(self) -> None:
        self.proposition = PropositionAdmissionSC3DPMinimaleFactory(matricule_candidat='user1')
        self.proposition_repository = PropositionInMemoryRepository()
        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.addCleanup(self.groupe_de_supervision_repository.reset)
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = VerifierPropositionCommand(uuid_proposition='uuid-SC3DP')

    def test_should_verifier_etre_ok(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.proposition.uuid)

    def test_should_retourner_erreur_si_identification_pas_completee(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP')
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), IdentificationNonCompleteeException)
