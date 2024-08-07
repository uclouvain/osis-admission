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
from django.test import SimpleTestCase

from admission.ddd.admission.formation_continue.commands import AnnulerPropositionCommand
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.formation_continue.domain.validator.exceptions import (
    AnnulerPropositionTransitionStatutException,
)
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class AnnulerPropositionTestCase(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.cmd = AnnulerPropositionCommand(
            uuid_proposition='uuid-USCC2',
            gestionnaire="gestionnaire",
            objet_message="objet",
            corps_message="corps",
            motif="foo",
        )

    def test_should_annuler(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(proposition.statut, ChoixStatutPropositionContinue.ANNULEE)
        self.assertEqual(proposition.checklist_actuelle.decision.statut, ChoixStatutChecklist.GEST_BLOCAGE)
        self.assertDictEqual(proposition.checklist_actuelle.decision.extra, {'blocage': 'canceled'})
        self.assertEqual(proposition.motif_d_annulation, "foo")

    def test_should_renvoyer_erreur_si_statut_cloture(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC2'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.GEST_BLOCAGE
        proposition.checklist_actuelle.decision.extra = {'blocage': 'closed'}

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

            self.assertIn(AnnulerPropositionTransitionStatutException, context.exception.exceptions)
