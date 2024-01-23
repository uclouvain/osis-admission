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
import uuid

import attr
from django.test import SimpleTestCase

from admission.ddd.admission.domain.validator.exceptions import BourseNonTrouveeException
from admission.ddd.admission.formation_generale.commands import ModifierChoixFormationParGestionnaireCommand
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PropositionNonTrouveeException,
)
from admission.infrastructure.admission.domain.service.in_memory.bourse import BourseInMemoryTranslator
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestModifierChoixFormationParGestionnaireService(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = ModifierChoixFormationParGestionnaireCommand(
            gestionnaire='0123456789',
            bourse_erasmus_mundus=BourseInMemoryTranslator.bourse_em_1.entity_id.uuid,
            bourse_internationale=BourseInMemoryTranslator.bourse_ifg_2.entity_id.uuid,
            bourse_double_diplome=BourseInMemoryTranslator.bourse_dd_2.entity_id.uuid,
            reponses_questions_specifiques={'35db2d60-9874-41fc-9f5a-ebfea38277d0': 'valeur'},
            uuid_proposition='uuid-BACHELIER-ECO1',
        )

    def test_should_modifier_choix_formation(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.EN_BROUILLON)
        self.assertEqual(proposition.bourse_erasmus_mundus_id.uuid, self.cmd.bourse_erasmus_mundus)
        self.assertEqual(proposition.bourse_internationale_id.uuid, self.cmd.bourse_internationale)
        self.assertEqual(proposition.bourse_double_diplome_id.uuid, self.cmd.bourse_double_diplome)
        self.assertEqual(proposition.reponses_questions_specifiques, self.cmd.reponses_questions_specifiques)

    def test_should_empecher_si_proposition_non_trouvee(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='INCONNUE')
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_bourse_erasmus_invalide(self):
        cmd = attr.evolve(self.cmd, bourse_erasmus_mundus=str(uuid.uuid4()))
        with self.assertRaises(BourseNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_bourse_double_diplomation_invalide(self):
        cmd = attr.evolve(self.cmd, bourse_double_diplome=str(uuid.uuid4()))
        with self.assertRaises(BourseNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_bourse_internationale_invalide(self):
        cmd = attr.evolve(self.cmd, bourse_internationale=str(uuid.uuid4()))
        with self.assertRaises(BourseNonTrouveeException):
            self.message_bus.invoke(cmd)
