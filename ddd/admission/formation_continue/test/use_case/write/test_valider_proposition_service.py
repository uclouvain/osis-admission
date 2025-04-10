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
from unittest.mock import patch

import mock
from django.test import SimpleTestCase

from admission.ddd.admission.domain.validator.exceptions import EnQuarantaineException
from admission.ddd.admission.dtos.merge_proposal import MergeProposalDTO
from admission.ddd.admission.formation_continue.commands import AnnulerPropositionCommand, ValiderPropositionCommand
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.formation_continue.domain.validator.exceptions import (
    ApprouverPropositionTransitionStatutException,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.person_merge_proposal import PersonMergeStatus


class ValiderPropositionTestCase(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.cmd = ValiderPropositionCommand(
            uuid_proposition='uuid-USCC22',
            gestionnaire="gestionnaire",
            objet_message="objet",
            corps_message="corps",
        )

        # Mock publish
        patcher = mock.patch('infrastructure.utils.MessageBus.publish')
        self.mock_publish = patcher.start()
        self.addCleanup(patcher.stop)

    def test_should_valider(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(proposition.statut, ChoixStatutPropositionContinue.INSCRIPTION_AUTORISEE)
        self.assertEqual(proposition.checklist_actuelle.decision.statut, ChoixStatutChecklist.GEST_REUSSITE)

    def test_should_valider_si_statut_a_valider(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC22'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.GEST_EN_COURS
        proposition.checklist_actuelle.decision.extra = {'en_cours': 'to_validate'}

        proposition_id = self.message_bus.invoke(self.cmd)
        updated_proposition = self.proposition_repository.get(proposition.entity_id)  # type: Proposition
        self.assertEqual(proposition_id, updated_proposition.entity_id)
        self.assertEqual(updated_proposition.statut, ChoixStatutPropositionContinue.INSCRIPTION_AUTORISEE)
        self.assertEqual(updated_proposition.checklist_actuelle.decision.statut, ChoixStatutChecklist.GEST_REUSSITE)

    def test_should_renvoyer_erreur_si_statut_cloture(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC22'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.GEST_BLOCAGE
        proposition.checklist_actuelle.decision.extra = {'blocage': 'closed'}

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertIsInstance(context.exception.exceptions.pop(), ApprouverPropositionTransitionStatutException)

    def test_should_renvoyer_erreur_si_statut_valide(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC22'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.GEST_EN_COURS
        proposition.checklist_actuelle.decision.extra = {'en_cours': 'taken_in_charge'}

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertIsInstance(context.exception.exceptions.pop(), ApprouverPropositionTransitionStatutException)

    def test_should_renvoyer_erreur_si_statut_en_attente(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC22'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.GEST_EN_COURS
        proposition.checklist_actuelle.decision.extra = {'en_cours': 'on_hold'}

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertIsInstance(context.exception.exceptions.pop(), ApprouverPropositionTransitionStatutException)

    def test_should_renvoyer_erreur_si_statut_refuse(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC22'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.GEST_BLOCAGE
        proposition.checklist_actuelle.decision.extra = {'blocage': 'denied'}

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertIsInstance(context.exception.exceptions.pop(), ApprouverPropositionTransitionStatutException)

    def test_should_renvoyer_erreur_si_statut_annule(self):
        proposition: Proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-USCC22'))
        proposition.checklist_actuelle.decision.statut = ChoixStatutChecklist.GEST_BLOCAGE
        proposition.checklist_actuelle.decision.extra = {'blocage': 'canceled'}

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertIsInstance(context.exception.exceptions.pop(), ApprouverPropositionTransitionStatutException)

    def test_should_lever_exception_si_quarantaine(self):
        with patch.object(
            ProfilCandidatInMemoryTranslator,
            'get_merge_proposal',
            return_value=MergeProposalDTO(
                status=PersonMergeStatus.ERROR.name,
                validation={},
            ),
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), EnQuarantaineException)
