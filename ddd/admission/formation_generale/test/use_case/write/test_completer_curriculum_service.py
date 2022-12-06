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
from django.test import SimpleTestCase

from admission.ddd.admission.formation_generale.commands import CompleterCurriculumCommand
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PropositionNonTrouveeException,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestCompleterCurriculumService(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = CompleterCurriculumCommand(
            uuid_proposition='uuid-BACHELIER-ECO1',
            continuation_cycle_bachelier=True,
            attestation_continuation_cycle_bachelier=['new_file.pdf'],
            curriculum=['new_file.pdf'],
            equivalence_diplome=['new_file.pdf'],
            reponses_questions_specifiques={
                '1': 'answer_1',
                '2': 'answer_2',
            },
        )

    def test_should_completer_curriculum(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(proposition.reponses_questions_specifiques, self.cmd.reponses_questions_specifiques)
        self.assertEqual(proposition.curriculum, self.cmd.curriculum)
        self.assertEqual(proposition.continuation_cycle_bachelier, self.cmd.continuation_cycle_bachelier)
        self.assertEqual(
            proposition.attestation_continuation_cycle_bachelier,
            self.cmd.attestation_continuation_cycle_bachelier,
        )
        self.assertEqual(proposition.equivalence_diplome, self.cmd.equivalence_diplome)

    def test_should_vider_curriculum(self):
        cmd = attr.evolve(
            self.cmd,
            curriculum=[],
            reponses_questions_specifiques={},
            continuation_cycle_bachelier=None,
            attestation_continuation_cycle_bachelier=[],
            equivalence_diplome=[],
        )
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(proposition.reponses_questions_specifiques, {})
        self.assertEqual(proposition.curriculum, [])
        self.assertEqual(proposition.continuation_cycle_bachelier, None)
        self.assertEqual(proposition.attestation_continuation_cycle_bachelier, [])
        self.assertEqual(proposition.equivalence_diplome, [])

    def test_should_empecher_si_proposition_non_trouvee(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='INCONNUE')
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(cmd)
