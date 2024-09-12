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

import attr
from django.test import SimpleTestCase

from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.doctorat.preparation.commands import ModifierChecklistChoixFormationCommand
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    PropositionNonTrouveeException,
    DoctoratNonTrouveException,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestModifierChecklistChoixFormationPropositionService(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = ModifierChecklistChoixFormationCommand(
            gestionnaire='0123456789',
            sigle_formation='AGRO3DP',
            annee_formation=2022,
            uuid_proposition='uuid-SC3DP-confirmee',
            type_demande='ADMISSION',
        )

    def test_should_modifier_choix_formation(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.formation_id.sigle, self.cmd.sigle_formation)
        self.assertEqual(proposition.type_demande, TypeDemande[self.cmd.type_demande])

    def test_should_empecher_si_proposition_non_trouvee(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='INCONNUE')
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_formation_non_trouvee(self):
        cmd = attr.evolve(self.cmd, sigle_formation='INCONNUE')
        with self.assertRaises(DoctoratNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_pas_formation_doctorale(self):
        cmd = attr.evolve(self.cmd, sigle_formation='CERTIF-BUS')
        with self.assertRaises(DoctoratNonTrouveException):
            self.message_bus.invoke(cmd)
