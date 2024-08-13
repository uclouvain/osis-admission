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
import uuid
from datetime import datetime
from unittest import mock

from django.test import TestCase
from waffle.testutils import override_switch

from admission.ddd.admission.commands import RetrieveListeTicketsEnAttenteQuery, \
    RetrieveAndStoreStatutTicketPersonneFromDigitCommand, RecupererMatriculeDigitQuery
from admission.ddd.admission.dtos.statut_ticket_personne import StatutTicketPersonneDTO
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.tasks import retrieve_digit_tickets_status
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.models.enums.civil_state import CivilState
from base.models.enums.person_address_type import PersonAddressType
from base.models.person_creation_ticket import PersonTicketCreation, PersonTicketCreationStatus
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_address import PersonAddressFactory


@override_switch('fusion-digit', active=True)
class TestRetrieveDigitTicketsStatus(TestCase):
    def setUp(self):
        self.personne_compte_temporaire = PersonFactory(global_id='89745632')
        self.person_merge_proposal = PersonMergeProposal.objects.create(
            original_person=self.personne_compte_temporaire,
            proposal_merge_person=None,
            status=PersonMergeStatus.NO_MATCH.name,
            similarity_result=[],
            last_similarity_result_update=datetime.now(),
            professional_curex_to_merge=[],
            educational_curex_to_merge=[],
            validation={'valid': 'true', 'errors': []}
        )
        self.ticket_digit = PersonTicketCreation.objects.create(
            uuid=uuid.uuid4(),
            status=PersonTicketCreationStatus.CREATED.name,
            person=self.personne_compte_temporaire,
        )

        self.admission = GeneralEducationAdmissionFactory(
            candidate=self.personne_compte_temporaire,
            type_demande=TypeDemande.INSCRIPTION.name,
        )
        self._mock_message_bus()
        self._mock_injection_signaletique()

    def _mock_message_bus(self):
        self.patch_message_bus = mock.patch(
            'infrastructure.messages_bus.message_bus_instance.invoke',
            side_effect=self.__mock_message_bus_invoke
        )
        self.message_bus_mocked = self.patch_message_bus.start()
        self.addCleanup(self.patch_message_bus.stop)

    def _mock_injection_signaletique(self):
        self.patch_injection_signaletique = mock.patch(
            'admission.tasks.retrieve_digit_tickets_status._injecter_signaletique_a_epc',
            side_effect=None
        )
        self.injection_signaletique_mocked = self.patch_injection_signaletique.start()
        self.addCleanup(self.patch_injection_signaletique.stop)

    def __mock_message_bus_invoke(self, cmd):
        if isinstance(cmd, RetrieveListeTicketsEnAttenteQuery):
            return [
                StatutTicketPersonneDTO(
                    uuid=self.ticket_digit.uuid,
                    request_id=None,
                    matricule=self.ticket_digit.person.global_id,
                    noma='47602400',
                    nom=self.ticket_digit.person.last_name,
                    prenom=self.ticket_digit.person.first_name,
                    statut=self.ticket_digit.status,
                    type_fusion=self.ticket_digit.merge_type,
                    errors=[],
                )
            ]
        elif isinstance(cmd, RetrieveAndStoreStatutTicketPersonneFromDigitCommand):
            self.ticket_digit.status = PersonTicketCreationStatus.DONE.name
            self.ticket_digit.request_id = '1234567'
            self.ticket_digit.save()
            return self.ticket_digit.status
        elif isinstance(cmd, RecupererMatriculeDigitQuery):
            return "00345678"
        raise Exception(f"Unknown command {cmd}")

    def test_assert_change_only_global_id_and_external_id(self):
        retrieve_digit_tickets_status.run()

        self.personne_compte_temporaire.refresh_from_db()
        self.assertEqual(self.personne_compte_temporaire.global_id, '00345678')
        self.assertEqual(self.personne_compte_temporaire.external_id, 'osis.person_00345678')

    def test_assert_merge_with_existing_account_and_existing_in_osis(self):
        self.personne_compte_temporaire.global_id = '00345678'   # Set as internal account
        self.personne_compte_temporaire.save()

        personne_connue = PersonFactory(global_id='00948959')

        self.person_merge_proposal.status = PersonMergeStatus.IN_PROGRESS.name   # Fusion acceptée par le gestionnaire
        self.person_merge_proposal.selected_global_id = personne_connue.global_id
        self.person_merge_proposal.proposal_merge_person = PersonFactory(
            global_id='',
            last_name='Durant',
            first_name='Thomas',
            middle_name='',
            birth_date=None,
            birth_place='',
            email='thomas.durant@gmail.com',
            gender='M',
            sex='M',
            civil_state=CivilState.SINGLE.name,
            country_of_citizenship=None,
            national_number='',
            id_card_number='',
            passport_number='',
            last_registration_id='',
            id_card_expiry_date=None,
            passport_expiry_date=None,
        )
        self.person_merge_proposal.save()

        retrieve_digit_tickets_status.run()

