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

from admission.ddd.admission.formation_continue.commands import MettreAValiderCommand
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.formation_continue.domain.validator.exceptions import (
    MettreAValiderTransitionStatutException,
)
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class MettreAValiderTestCase(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.cmd = MettreAValiderCommand(
            uuid_proposition='uuid-USCC22',
            gestionnaire="gestionnaire",
        )

    def test_should_mettre_a_valider_si_statut_approuve_par_fac(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition

        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(proposition.checklist_actuelle.decision.statut, ChoixStatutChecklist.GEST_EN_COURS)
        self.assertDictEqual(proposition.checklist_actuelle.decision.extra, {'en_cours': 'to_validate'})

    def test_should_renvoyer_erreur_si_statut_a_traiter(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC22'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.INITIAL_CANDIDAT
        proposition.checklist_actuelle.decision.extra = {}

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

            self.assertIn(MettreAValiderTransitionStatutException, context.exception.exceptions)

    def test_should_renvoyer_erreur_si_statut_prise_en_charge(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC22'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.GEST_EN_COURS
        proposition.checklist_actuelle.decision.extra = {'en_cours': 'taken_in_charge'}

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

            self.assertIn(MettreAValiderTransitionStatutException, context.exception.exceptions)

    def test_should_renvoyer_erreur_si_statut_cloture(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC22'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.GEST_BLOCAGE
        proposition.checklist_actuelle.decision.extra = {'blocage': 'closed'}

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

            self.assertIn(MettreAValiderTransitionStatutException, context.exception.exceptions)

    def test_should_renvoyer_erreur_si_statut_valide(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC22'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.GEST_EN_COURS
        proposition.checklist_actuelle.decision.extra = {'en_cours': 'taken_in_charge'}

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

            self.assertIn(MettreAValiderTransitionStatutException, context.exception.exceptions)

    def test_should_renvoyer_erreur_si_statut_a_valider(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC22'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.GEST_EN_COURS
        proposition.checklist_actuelle.decision.extra = {'en_cours': 'to_validate'}

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

            self.assertIn(MettreAValiderTransitionStatutException, context.exception.exceptions)

    def test_should_renvoyer_erreur_si_statut_en_attente(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC22'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.GEST_EN_COURS
        proposition.checklist_actuelle.decision.extra = {'en_cours': 'on_hold'}

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

            self.assertIn(MettreAValiderTransitionStatutException, context.exception.exceptions)

    def test_should_renvoyer_erreur_si_statut_refuse(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC22'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.GEST_BLOCAGE
        proposition.checklist_actuelle.decision.extra = {'blocage': 'denied'}

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

            self.assertIn(MettreAValiderTransitionStatutException, context.exception.exceptions)

    def test_should_renvoyer_erreur_si_statut_annule(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC22'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.GEST_BLOCAGE
        proposition.checklist_actuelle.decision.extra = {'blocage': 'canceled'}

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

            self.assertIn(MettreAValiderTransitionStatutException, context.exception.exceptions)
