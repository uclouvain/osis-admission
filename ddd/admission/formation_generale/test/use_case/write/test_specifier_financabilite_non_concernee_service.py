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

import freezegun
from django.test import TestCase

from admission.ddd.admission.formation_generale.commands import (
    SpecifierFinancabiliteNonConcerneeCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutChecklist
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


@freezegun.freeze_time('2020-11-01')
class TestSpecifierFinancabiliteNonConcernee(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.message_bus = message_bus_in_memory_instance

    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.proposition = self.proposition_repository.get(
            PropositionIdentity(
                uuid='uuid-CERTIFICATE-CONFIRMED',
            ),
        )

        self.command = SpecifierFinancabiliteNonConcerneeCommand(
            uuid_proposition='uuid-CERTIFICATE-CONFIRMED',
            etabli_par='uuid-GESTIONNAIRE',
            gestionnaire='0123456789',
        )

    def test_should_specifier_etre_non_specifie(self):
        proposition_id = self.message_bus.invoke(self.command)

        proposition = self.proposition_repository.get(proposition_id)

        # Résultat de la commande
        self.assertEqual(proposition_id.uuid, proposition.entity_id.uuid)

        # Proposition mise à jour
        self.assertIsNone(proposition.financabilite_regle)
        self.assertEqual(proposition.financabilite_regle_etabli_par, 'uuid-GESTIONNAIRE')
        self.assertEqual(proposition.checklist_actuelle.financabilite.statut, ChoixStatutChecklist.INITIAL_NON_CONCERNE)
