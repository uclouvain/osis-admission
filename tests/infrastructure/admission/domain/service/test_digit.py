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
import contextlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import mock
from django.db import transaction
from django.test import override_settings, TransactionTestCase
from waffle.testutils import override_switch

from admission.ddd.admission.commands import SoumettreTicketPersonneCommand
from admission.ddd.admission.domain.validator.exceptions import NotInAccountCreationPeriodException
from admission.ddd.admission.formation_continue.test.factory.proposition import PropositionFactory
from admission.ddd.admission.formation_generale.domain.validator.exceptions import \
    PremierePropositionSoumisesNonTrouveeException
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.formation import \
    FormationGeneraleInMemoryTranslator
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import \
    PropositionInMemoryRepository
from base.models.person_merge_proposal import PersonMergeProposal
from base.tests.factories.person import PersonFactory
from infrastructure.messages_bus import message_bus_instance
from infrastructure.shared_kernel.signaletique_etudiant.repository.in_memory.compteur_noma import \
    CompteurAnnuelPourNomaInMemoryRepository


@override_switch('fusion-digit', active=True)
@override_settings(USE_CELERY=False)
class SoumettreTicketsEnParalleleTestCase(TransactionTestCase):
    def setUp(self):
        self.patch_peut_soumettre = mock.patch(
            'admission.ddd.admission.domain.service.i_digit.IDigitService.verifier_peut_soumettre_ticket_creation',
        )
        self.peut_soumettre_mocked = self.patch_peut_soumettre.start()
        self.addCleanup(self.patch_peut_soumettre.stop)

        self.person = PersonFactory()
        self.pmp = PersonMergeProposal(original_person=self.person, last_similarity_result_update=datetime.now())
        self.pmp.save()

        self.formation_translator = FormationGeneraleInMemoryTranslator()

        proposition = PropositionFactory(
            matricule_candidat=self.person.global_id,
            formation_id=self.formation_translator.trainings[0].entity_id,
            annee_calculee=2024,
        )

        self.proposition_repository = PropositionInMemoryRepository()
        self.proposition_repository.save(proposition)

        self.noma_repository = CompteurAnnuelPourNomaInMemoryRepository()

        self.__mock_service_bus()

    def __mock_service_bus(self):
        message_bus_patcher = mock.patch.multiple(
            'admission.infrastructure.admission.formation_generale.handlers',
            PropositionRepository=lambda: self.proposition_repository,
            FormationGeneraleTranslator=lambda: self.formation_translator,
            CompteurAnnuelPourNomaRepository=lambda: self.noma_repository,
        )
        message_bus_patcher.start()
        self.addCleanup(message_bus_patcher.stop)
        self.message_bus = message_bus_instance

    def test_should_handle_lock_on_person_merge_proposal_and_not_create_a_new_noma(self):
        def submit_person_ticket():
            with transaction.atomic():
                with contextlib.suppress(
                        PremierePropositionSoumisesNonTrouveeException, NotInAccountCreationPeriodException
                ):
                    cmd = SoumettreTicketPersonneCommand(global_id=self.person.global_id)
                    self.message_bus.invoke(cmd)

        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(submit_person_ticket)
            executor.submit(submit_person_ticket)

        self.pmp.refresh_from_db()
        self.assertEqual(self.pmp.registration_id_sent_to_digit, '00002400')
