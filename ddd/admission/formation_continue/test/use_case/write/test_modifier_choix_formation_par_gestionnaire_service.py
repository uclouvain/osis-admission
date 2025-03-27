# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import mock

import attr
from django.test import SimpleTestCase

from admission.ddd.admission.formation_continue.commands import (
    ModifierChoixFormationParGestionnaireCommand,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixMoyensDecouverteFormation,
)
from admission.ddd.admission.formation_continue.domain.validator.exceptions import (
    FormationNonTrouveeException,
    PropositionNonTrouveeException,
)
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)


class TestModifierChoixFormationParGestionnaireService(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = ModifierChoixFormationParGestionnaireCommand(
            sigle_formation='USCC4',
            annee_formation=2022,
            uuid_proposition='uuid-USCC1',
            motivations='Motivations',
            moyens_decouverte_formation=[
                ChoixMoyensDecouverteFormation.COURRIER_PERSONNALISE.name,
                ChoixMoyensDecouverteFormation.AUTRE.name,
            ],
            autre_moyen_decouverte_formation='Autre moyen',
            marque_d_interet=True,
            gestionnaire="gestionnaire",
            reponses_questions_specifiques={'q1': 'v1'},
        )

        # Mock publish
        patcher = mock.patch('infrastructure.utils.MessageBus.publish')
        self.mock_publish = patcher.start()
        self.addCleanup(patcher.stop)

    def test_should_modifier_choix_formation(self):
        proposition_id = self.message_bus.invoke(self.cmd)

        proposition = self.proposition_repository.get(proposition_id)

        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(proposition.formation_id.sigle, 'USCC4')
        self.assertEqual(proposition.formation_id.annee, 2022)
        self.assertEqual(proposition.annee_calculee, 2022)
        self.assertEqual(proposition.motivations, 'Motivations')
        self.assertEqual(
            proposition.moyens_decouverte_formation,
            [
                ChoixMoyensDecouverteFormation.COURRIER_PERSONNALISE,
                ChoixMoyensDecouverteFormation.AUTRE,
            ],
        )
        self.assertEqual(proposition.autre_moyen_decouverte_formation, 'Autre moyen')
        self.assertEqual(proposition.marque_d_interet, True)
        self.assertEqual(proposition.auteur_derniere_modification, 'gestionnaire')
        self.assertEqual(proposition.reponses_questions_specifiques, {'q1': 'v1'})

    def test_should_empecher_si_proposition_non_trouvee(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='INCONNUE')
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_formation_non_trouvee(self):
        cmd = attr.evolve(self.cmd, sigle_formation='INCONNUE')
        with self.assertRaises(FormationNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_pas_formation_continue(self):
        cmd = attr.evolve(self.cmd, sigle_formation='ESP3DP-MASTER')
        with self.assertRaises(FormationNonTrouveeException):
            self.message_bus.invoke(cmd)
