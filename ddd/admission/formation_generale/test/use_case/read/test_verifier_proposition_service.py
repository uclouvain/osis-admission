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
from unittest import TestCase

from admission.ddd.admission.domain.validator.exceptions import ConditionsAccessNonRempliesException
from admission.ddd.admission.formation_generale.commands import VerifierPropositionCommand
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestVerifierPropositionService(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def test_should_verifier_etre_ok_si_complet(self):
        cmd = VerifierPropositionCommand(uuid_proposition="uuid-ECGE3DP")
        proposition_id = self.message_bus.invoke(cmd)
        self.assertEqual(proposition_id.uuid, "uuid-ECGE3DP")

    def test_should_retourner_erreur_si_conditions_acces_non_remplies(self):
        cmd = VerifierPropositionCommand(uuid_proposition='uuid-SC3DP')
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), ConditionsAccessNonRempliesException)
