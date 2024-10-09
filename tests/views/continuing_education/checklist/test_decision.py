# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from email import message_from_string

import freezegun
import mock
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from osis_history.models import HistoryEntry
from osis_notification.models import EmailNotification

from admission.contrib.models import ContinuingEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutChecklist,
    ChoixStatutPropositionContinue,
    ChoixMotifAttente,
    ChoixMotifRefus,
)
from admission.forms.admission.continuing_education.checklist import (
    DecisionFacApprovalForm,
    DecisionFacApprovalChoices,
    DecisionHoldForm,
    DecisionDenyForm,
    DecisionCancelForm,
    DecisionValidationForm,
    CloseForm,
)
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
    ContinuingEducationTrainingFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import CentralManagerRoleFactory, ProgramManagerRoleFactory
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from education_group.auth.scope import Scope


class ChecklistViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)

        cls.training = ContinuingEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
            education_group_type__name=TrainingType.MASTER_MA_120.name,
        )
        cls.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            submitted=True,
        )
        cls.candidate = cls.continuing_admission.candidate

        cls.iufc_manager_user = CentralManagerRoleFactory(
            entity=cls.first_doctoral_commission, scopes=[Scope.IUFC.name]
        ).person.user

        cls.fac_manager_user = ProgramManagerRoleFactory(
            education_group=cls.training.education_group,
        ).person.user

        cls.default_headers = {'HTTP_HX-Request': 'true'}

        cls.file_metadata = {
            'name': 'myfile',
            'mimetype': PDF_MIME_TYPE,
            'explicit_name': 'My file name',
            'author': cls.iufc_manager_user.person.global_id,
        }

    def setUp(self) -> None:
        patcher = mock.patch('admission.templatetags.admission.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('admission.templatetags.admission.get_remote_metadata', return_value=self.file_metadata)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {uuid: f'token-{index}' for index, uuid in enumerate(uuids)}
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.get_remote_metadata', return_value=self.file_metadata)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {token: self.file_metadata for token in tokens}
        self.addCleanup(patcher.stop)

        self.continuing_admission.last_update_author = None

    #### IUFC MANAGER

    def test_get_hold_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-hold',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context['decision_hold_form'], DecisionHoldForm)

    def test_valid_post_hold_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-hold',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'decision-hold-reason': ChoixMotifAttente.COMPLET.name,
                'decision-hold-subject': 'subject',
                'decision-hold-body': 'body',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context['decision_hold_form'].is_valid())

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_EN_COURS.name,
        )
        self.assertDictEqual(
            self.continuing_admission.checklist['current']['decision']['extra'],
            {'en_cours': 'on_hold'},
        )
        self.assertEqual(self.continuing_admission.status, ChoixStatutPropositionContinue.EN_ATTENTE.name)
        self.assertEqual(self.continuing_admission.on_hold_reason, ChoixMotifAttente.COMPLET.name)
        self.assertEqual(self.continuing_admission.last_update_author, self.iufc_manager_user.person)

        # Check that a notification has been created
        notifications = EmailNotification.objects.filter(person=self.continuing_admission.candidate)
        self.assertEqual(len(notifications), 1)
        email_object = message_from_string(notifications[0].payload)
        self.assertEqual(email_object['To'], self.continuing_admission.candidate.private_email)

        # Check that two historic entries have been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 2)

        self.assertCountEqual(
            [entry.tags for entry in historic_entries],
            [['proposition', 'decision', 'status-changed'], ['proposition', 'decision', 'message']],
        )

    def test_get_to_validate_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-to-validate',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

    def test_valid_post_to_validate_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        self.continuing_admission.checklist['current']['decision'] = {
            'libelle': '',
            'enfants': [],
            'extra': {'en_cours': 'fac_approval'},
            'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
        }
        self.continuing_admission.save(update_fields=['checklist'])

        url = resolve_url(
            'admission:continuing-education:decision-to-validate',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context['form'].is_valid())

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_EN_COURS.name,
        )
        self.assertDictEqual(
            self.continuing_admission.checklist['current']['decision']['extra'],
            {'en_cours': 'to_validate'},
        )

    def test_get_fac_approval_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-fac-approval',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context['decision_fac_approval_form'], DecisionFacApprovalForm)

    def test_post_fac_approval_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-fac-approval',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'decision-fac-approval-accepter_la_demande': DecisionFacApprovalChoices.SANS_CONDITION.name,
                'decision-fac-approval-condition_acceptation': 'foobar',
                'decision-fac-approval-subject': 'subject',
                'decision-fac-approval-body': 'body',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context['decision_fac_approval_form'].is_valid())

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_EN_COURS.name,
        )
        self.assertEqual(self.continuing_admission.approval_condition_by_faculty, 'foobar')
        self.assertEqual(self.continuing_admission.last_update_author, self.iufc_manager_user.person)

        # Check that a notification has been created
        notifications = EmailNotification.objects.filter(person=self.continuing_admission.candidate)
        self.assertEqual(len(notifications), 1)
        email_object = message_from_string(notifications[0].payload)
        self.assertEqual(email_object['To'], self.continuing_admission.candidate.private_email)

        # Check that two historic entries have been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 2)

        self.assertCountEqual(
            [entry.tags for entry in historic_entries],
            [['proposition', 'decision', 'status-changed'], ['proposition', 'decision', 'message']],
        )

    def test_get_deny_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-deny',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context['decision_deny_form'], DecisionDenyForm)

    def test_post_deny_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-deny',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'decision-deny-reason': ChoixMotifRefus.FULL.name,
                'decision-deny-subject': 'subject',
                'decision-deny-body': 'body',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context['decision_deny_form'].is_valid())

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertDictEqual(
            self.continuing_admission.checklist['current']['decision']['extra'],
            {'blocage': 'denied'},
        )
        self.assertEqual(self.continuing_admission.status, ChoixStatutPropositionContinue.INSCRIPTION_REFUSEE.name)
        self.assertEqual(self.continuing_admission.refusal_reason, ChoixMotifRefus.FULL.name)
        self.assertEqual(self.continuing_admission.last_update_author, self.iufc_manager_user.person)

        # Check that a notification has been created
        notifications = EmailNotification.objects.filter(person=self.continuing_admission.candidate)
        self.assertEqual(len(notifications), 1)
        email_object = message_from_string(notifications[0].payload)
        self.assertEqual(email_object['To'], self.continuing_admission.candidate.private_email)

        # Check that two historic entries have been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 2)

        self.assertCountEqual(
            [entry.tags for entry in historic_entries],
            [['proposition', 'decision', 'status-changed'], ['proposition', 'decision', 'message']],
        )

    def test_get_cancel_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-cancel',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context['decision_cancel_form'], DecisionCancelForm)

    def test_post_cancel_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-cancel',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'decision-cancel-reason': 'foobar',
                'decision-cancel-subject': 'subject',
                'decision-cancel-body': 'body',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context['decision_cancel_form'].is_valid())

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertDictEqual(
            self.continuing_admission.checklist['current']['decision']['extra'],
            {'blocage': 'canceled'},
        )
        self.assertEqual(self.continuing_admission.status, ChoixStatutPropositionContinue.ANNULEE.name)
        self.assertEqual(self.continuing_admission.cancel_reason, 'foobar')
        self.assertEqual(self.continuing_admission.last_update_author, self.iufc_manager_user.person)

        # Check that a notification has been created
        notifications = EmailNotification.objects.filter(person=self.continuing_admission.candidate)
        self.assertEqual(len(notifications), 1)
        email_object = message_from_string(notifications[0].payload)
        self.assertEqual(email_object['To'], self.continuing_admission.candidate.private_email)

        # Check that two historic entries have been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 2)

        self.assertCountEqual(
            [entry.tags for entry in historic_entries],
            [['proposition', 'decision', 'status-changed'], ['proposition', 'decision', 'message']],
        )

    def test_get_validation_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-validation',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context['decision_validation_form'], DecisionValidationForm)

    def test_post_validation_iufc(self):
        self.continuing_admission.checklist['current']['decision'] = {
            'libelle': '',
            'enfants': [],
            'extra': {'en_cours': 'fac_approval'},
            'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
        }
        self.continuing_admission.save(update_fields=['checklist'])
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-validation',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'decision-validation-subject': 'subject',
                'decision-validation-body': 'body',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context['decision_validation_form'].is_valid())

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(self.continuing_admission.status, ChoixStatutPropositionContinue.INSCRIPTION_AUTORISEE.name)
        self.assertEqual(self.continuing_admission.last_update_author, self.iufc_manager_user.person)

        # Check that a notification has been created
        notifications = EmailNotification.objects.filter(person=self.continuing_admission.candidate)
        self.assertEqual(len(notifications), 1)
        email_object = message_from_string(notifications[0].payload)
        self.assertEqual(email_object['To'], self.continuing_admission.candidate.private_email)

        # Check that two historic entries have been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 2)

        self.assertCountEqual(
            [entry.tags for entry in historic_entries],
            [['proposition', 'decision', 'status-changed'], ['proposition', 'decision', 'message']],
        )

    def test_get_close_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-close',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context['decision_close_form'], CloseForm)

    def test_post_close_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-close',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertDictEqual(
            self.continuing_admission.checklist['current']['decision']['extra'],
            {'blocage': 'closed'},
        )
        self.assertEqual(self.continuing_admission.status, ChoixStatutPropositionContinue.CLOTUREE.name)
        self.assertEqual(self.continuing_admission.last_update_author, self.iufc_manager_user.person)

        # Check that one historic entry has been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 1)

        self.assertEqual(
            historic_entries[0].tags,
            ['proposition', 'decision', 'status-changed'],
        )

    @freezegun.freeze_time('2024-01-01')
    def test_post_close_iufc_during_a_documents_request(self):
        self.client.force_login(user=self.iufc_manager_user)

        self.continuing_admission.status = ChoixStatutPropositionContinue.A_COMPLETER_POUR_FAC.name
        self.continuing_admission.requested_documents = {
            'CURRICULUM.CURRICULUM': {
                'last_actor': '00321234',
                'reason': 'Le document est à mettre à jour.',
                'type': TypeEmplacementDocument.NON_LIBRE.name,
                'last_action_at': '2023-01-02T00:00:00',
                'status': StatutEmplacementDocument.RECLAME.name,
                'requested_at': '2023-01-02T00:00:00',
                'deadline_at': '2023-01-19',
                'automatically_required': False,
                'related_checklist_tab': '',
                'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
            }
        }

        self.continuing_admission.save(update_fields=['status', 'requested_documents'])

        url = resolve_url(
            'admission:continuing-education:decision-close',
            uuid=self.continuing_admission.uuid,
        )

        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertDictEqual(
            self.continuing_admission.checklist['current']['decision']['extra'],
            {'blocage': 'closed'},
        )
        self.assertEqual(self.continuing_admission.status, ChoixStatutPropositionContinue.CLOTUREE.name)
        self.assertEqual(self.continuing_admission.last_update_author, self.iufc_manager_user.person)

        # Check that no document is requested anymore
        self.assertEqual(
            self.continuing_admission.requested_documents['CURRICULUM.CURRICULUM'],
            {
                'last_actor': self.iufc_manager_user.person.global_id,
                'reason': 'Le document est à mettre à jour.',
                'type': TypeEmplacementDocument.NON_LIBRE.name,
                'last_action_at': '2024-01-01T00:00:00',
                'status': StatutEmplacementDocument.RECLAMATION_ANNULEE.name,
                'requested_at': '',
                'deadline_at': '',
                'automatically_required': False,
                'related_checklist_tab': '',
                'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
            },
        )

        # Check that one historic entry has been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 2)

        self.assertCountEqual(
            [entry.tags for entry in historic_entries],
            [['proposition', 'decision', 'status-changed'], ['proposition', 'status-changed']],
        )

    def test_get_to_be_processed_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-change-status-to-be-processed',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'admission/continuing_education/includes/checklist/decision_to_be_processed_form.html'
        )

    def test_post_to_be_processed_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-change-status-to-be-processed',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.INITIAL_CANDIDAT.name,
        )
        self.assertEqual(self.continuing_admission.status, ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertEqual(self.continuing_admission.last_update_author, self.iufc_manager_user.person)

        # Check that one historic entry has been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 1)

        self.assertEqual(
            historic_entries[0].tags,
            ['proposition', 'decision', 'status-changed'],
        )

    def test_get_taken_in_charge_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-change-status-taken-in-charge',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'admission/continuing_education/includes/checklist/decision_taken_in_charge_form.html'
        )

    def test_post_taken_in_charge_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-change-status-taken-in-charge',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_EN_COURS.name,
        )
        self.assertDictEqual(
            self.continuing_admission.checklist['current']['decision']['extra'],
            {'en_cours': 'taken_in_charge'},
        )
        self.assertEqual(self.continuing_admission.status, ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertEqual(self.continuing_admission.last_update_author, self.iufc_manager_user.person)

        # Check that one historic entry has been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 1)

        self.assertEqual(
            historic_entries[0].tags,
            ['proposition', 'decision', 'status-changed'],
        )

    def test_get_send_to_fac_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-send-to-fac',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'admission/continuing_education/includes/checklist/decision_send_to_fac_form.html'
        )

    def test_post_send_to_fac_iufc(self):
        self.client.force_login(user=self.iufc_manager_user)

        self.assertFalse(EmailNotification.objects.filter(person=self.fac_manager_user.person).exists())

        url = resolve_url(
            'admission:continuing-education:decision-send-to-fac',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'decision-send-to-fac-comment': 'foobar',
                'decision-send-to-fac-subject': 'subject',
                'decision-send-to-fac-body': 'body',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['decision_send_to_fac_form'].is_valid())

        notifications = EmailNotification.objects.filter(person=self.fac_manager_user.person)
        self.assertEqual(len(notifications), 1)
        email_object = message_from_string(notifications[0].payload)
        self.assertEqual(email_object['To'], self.fac_manager_user.person.email)

    #### FAC MANAGER

    def test_get_hold_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-hold',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context['decision_hold_form'], DecisionHoldForm)

    def test_post_hold_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-hold',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'decision-hold-reason': ChoixMotifAttente.COMPLET.name,
                'decision-hold-subject': 'subject',
                'decision-hold-body': 'body',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context['decision_hold_form'].is_valid())

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_EN_COURS.name,
        )
        self.assertDictEqual(
            self.continuing_admission.checklist['current']['decision']['extra'],
            {'en_cours': 'on_hold'},
        )
        self.assertEqual(self.continuing_admission.status, ChoixStatutPropositionContinue.EN_ATTENTE.name)
        self.assertEqual(self.continuing_admission.on_hold_reason, ChoixMotifAttente.COMPLET.name)
        self.assertEqual(self.continuing_admission.last_update_author, self.fac_manager_user.person)

        # Check that a notification has been created
        notifications = EmailNotification.objects.filter(person=self.continuing_admission.candidate)
        self.assertEqual(len(notifications), 1)
        email_object = message_from_string(notifications[0].payload)
        self.assertEqual(email_object['To'], self.continuing_admission.candidate.private_email)

        # Check that two historic entries have been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 2)

        self.assertCountEqual(
            [entry.tags for entry in historic_entries],
            [['proposition', 'decision', 'status-changed'], ['proposition', 'decision', 'message']],
        )

    def test_get_to_validate_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-to-validate',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_valid_post_to_validate_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        self.continuing_admission.checklist['current']['decision'] = {
            'libelle': '',
            'enfants': [],
            'extra': {'en_cours': 'fac_approval'},
            'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
        }
        self.continuing_admission.save(update_fields=['checklist'])

        url = resolve_url(
            'admission:continuing-education:decision-to-validate',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 403)

    def test_get_fac_approval_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-fac-approval',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context['decision_fac_approval_form'], DecisionFacApprovalForm)

    def test_post_fac_approval_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-fac-approval',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'decision-fac-approval-accepter_la_demande': DecisionFacApprovalChoices.SANS_CONDITION.name,
                'decision-fac-approval-condition_acceptation': 'foobar',
                'decision-fac-approval-subject': 'subject',
                'decision-fac-approval-body': 'body',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context['decision_fac_approval_form'].is_valid())

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_EN_COURS.name,
        )
        self.assertEqual(self.continuing_admission.approval_condition_by_faculty, 'foobar')
        self.assertEqual(self.continuing_admission.last_update_author, self.fac_manager_user.person)

        # Check that a notification has been created
        notifications = EmailNotification.objects.filter(person=self.continuing_admission.candidate)
        self.assertEqual(len(notifications), 1)
        email_object = message_from_string(notifications[0].payload)
        self.assertEqual(email_object['To'], self.continuing_admission.candidate.private_email)

        # Check that two historic entries have been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 2)

        self.assertCountEqual(
            [entry.tags for entry in historic_entries],
            [['proposition', 'decision', 'status-changed'], ['proposition', 'decision', 'message']],
        )

    def test_get_deny_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-deny',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context['decision_deny_form'], DecisionDenyForm)

    def test_post_deny_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-deny',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'decision-deny-reason': ChoixMotifRefus.FULL.name,
                'decision-deny-subject': 'subject',
                'decision-deny-body': 'body',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context['decision_deny_form'].is_valid())

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertDictEqual(
            self.continuing_admission.checklist['current']['decision']['extra'],
            {'blocage': 'denied'},
        )
        self.assertEqual(self.continuing_admission.status, ChoixStatutPropositionContinue.INSCRIPTION_REFUSEE.name)
        self.assertEqual(self.continuing_admission.refusal_reason, ChoixMotifRefus.FULL.name)
        self.assertEqual(self.continuing_admission.last_update_author, self.fac_manager_user.person)

        # Check that a notification has been created
        notifications = EmailNotification.objects.filter(person=self.continuing_admission.candidate)
        self.assertEqual(len(notifications), 1)
        email_object = message_from_string(notifications[0].payload)
        self.assertEqual(email_object['To'], self.continuing_admission.candidate.private_email)

        # Check that two historic entries have been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 2)

        self.assertCountEqual(
            [entry.tags for entry in historic_entries],
            [['proposition', 'decision', 'status-changed'], ['proposition', 'decision', 'message']],
        )

    def test_get_cancel_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-cancel',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context['decision_cancel_form'], DecisionCancelForm)

    def test_post_cancel_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-cancel',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'decision-cancel-reason': 'foobar',
                'decision-cancel-subject': 'subject',
                'decision-cancel-body': 'body',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context['decision_cancel_form'].is_valid())

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertDictEqual(
            self.continuing_admission.checklist['current']['decision']['extra'],
            {'blocage': 'canceled'},
        )
        self.assertEqual(self.continuing_admission.status, ChoixStatutPropositionContinue.ANNULEE.name)
        self.assertEqual(self.continuing_admission.cancel_reason, 'foobar')
        self.assertEqual(self.continuing_admission.last_update_author, self.fac_manager_user.person)

        # Check that a notification has been created
        notifications = EmailNotification.objects.filter(person=self.continuing_admission.candidate)
        self.assertEqual(len(notifications), 1)
        email_object = message_from_string(notifications[0].payload)
        self.assertEqual(email_object['To'], self.continuing_admission.candidate.private_email)

        # Check that two historic entries have been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 2)

        self.assertCountEqual(
            [entry.tags for entry in historic_entries],
            [['proposition', 'decision', 'status-changed'], ['proposition', 'decision', 'message']],
        )

    def test_get_validation_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-validation',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_post_validation_fac(self):
        self.continuing_admission.checklist['current']['decision'] = {
            'libelle': '',
            'enfants': [],
            'extra': {'en_cours': 'fac_approval'},
            'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
        }
        self.continuing_admission.save(update_fields=['checklist'])
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-validation',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'decision-validation-subject': 'subject',
                'decision-validation-body': 'body',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 403)

    def test_get_close_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-close',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context['decision_close_form'], CloseForm)

    def test_post_close_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-close',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertDictEqual(
            self.continuing_admission.checklist['current']['decision']['extra'],
            {'blocage': 'closed'},
        )
        self.assertEqual(self.continuing_admission.status, ChoixStatutPropositionContinue.CLOTUREE.name)
        self.assertEqual(self.continuing_admission.last_update_author, self.fac_manager_user.person)

        # Check that one historic entry has been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 1)

        self.assertEqual(
            historic_entries[0].tags,
            ['proposition', 'decision', 'status-changed'],
        )

    def test_get_to_be_processed_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-change-status-to-be-processed',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'admission/continuing_education/includes/checklist/decision_to_be_processed_form.html'
        )

    def test_post_to_be_processed_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-change-status-to-be-processed',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.INITIAL_CANDIDAT.name,
        )
        self.assertEqual(self.continuing_admission.status, ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertEqual(self.continuing_admission.last_update_author, self.fac_manager_user.person)

        # Check that one historic entry has been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 1)

        self.assertEqual(
            historic_entries[0].tags,
            ['proposition', 'decision', 'status-changed'],
        )

    def test_get_taken_in_charge_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-change-status-taken-in-charge',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'admission/continuing_education/includes/checklist/decision_taken_in_charge_form.html'
        )

    def test_post_taken_in_charge_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-change-status-taken-in-charge',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.continuing_admission.refresh_from_db()

        self.assertEqual(
            self.continuing_admission.checklist['current']['decision']['statut'],
            ChoixStatutChecklist.GEST_EN_COURS.name,
        )
        self.assertDictEqual(
            self.continuing_admission.checklist['current']['decision']['extra'],
            {'en_cours': 'taken_in_charge'},
        )
        self.assertEqual(self.continuing_admission.status, ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertEqual(self.continuing_admission.last_update_author, self.fac_manager_user.person)

        # Check that one historic entry has been created
        historic_entries = HistoryEntry.objects.filter(object_uuid=self.continuing_admission.uuid)
        self.assertEqual(len(historic_entries), 1)

        self.assertEqual(
            historic_entries[0].tags,
            ['proposition', 'decision', 'status-changed'],
        )

    def test_get_send_to_fac_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-send-to-fac',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_post_send_to_fac_fac(self):
        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:decision-send-to-fac',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'decision-send-to-fac-comment': 'foobar',
                'decision-send-to-fac-subject': 'subject',
                'decision-send-to-fac-body': 'body',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 403)
