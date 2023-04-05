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

from admission.ddd.admission.formation_generale.commands import (
    RecupererQuestionsSpecifiquesQuery as RecupererQuestionsSpecifiquesFormationGeneraleQuery,
)
from admission.ddd.admission.formation_continue.commands import (
    RecupererQuestionsSpecifiquesQuery as RecupererQuestionsSpecifiquesFormationContinueQuery,
)
from admission.ddd.admission.doctorat.preparation.commands import (
    RecupererQuestionsSpecifiquesQuery as RecupererQuestionsSpecifiquesFormationDoctoraleQuery,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestRecupererQuestionsSpecifiquesFormationGenerale(TestCase):
    def setUp(self) -> None:
        self.cmd = RecupererQuestionsSpecifiquesFormationGeneraleQuery(uuid_proposition='uuid-MASTER-SCI')
        self.message_bus = message_bus_in_memory_instance

    def test_should_recuperer_questions_specifiques_demande(self):
        questions = self.message_bus.invoke(self.cmd)
        self.assertEqual(len(questions), 6)


class TestRecupererQuestionsSpecifiquesFormationContinue(TestCase):
    def setUp(self) -> None:
        self.cmd = RecupererQuestionsSpecifiquesFormationContinueQuery(uuid_proposition='uuid-USCC1')
        self.message_bus = message_bus_in_memory_instance

    def test_should_recuperer_questions_specifiques_demande(self):
        questions = self.message_bus.invoke(self.cmd)
        self.assertEqual(len(questions), 6)


class TestRecupererQuestionsSpecifiquesFormationDoctorale(TestCase):
    def setUp(self) -> None:
        self.cmd = RecupererQuestionsSpecifiquesFormationDoctoraleQuery(uuid_proposition='uuid-SC3DP')
        self.message_bus = message_bus_in_memory_instance

    def test_should_recuperer_questions_specifiques_demande(self):
        questions = self.message_bus.invoke(self.cmd)
        self.assertEqual(len(questions), 5)
