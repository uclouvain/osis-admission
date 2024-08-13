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

import datetime
import uuid
from email import message_from_string
from typing import Optional

import freezegun
from django.shortcuts import resolve_url
from django.test import override_settings
from django.utils.translation import gettext
from osis_history.models import HistoryEntry
from osis_notification.models import EmailNotification

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.tests.views.common.detail_tabs.test_document import BaseDocumentViewTestCase
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.forms.utils.file_field import PDF_MIME_TYPE


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DocumentDetailTestCase(BaseDocumentViewTestCase):
    # Lists of documents
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_document_detail_sic_manager(self, frozen_time):
        self.init_documents(for_sic=True)

        self.client.force_login(user=self.second_sic_manager_user)

        url = resolve_url('admission:general-education:documents', uuid=self.general_admission.uuid)

        # Get the list and the request form
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.general_admission.uuid)
        self.assertTrue(len(response.context['documents']) > 0)

        form = response.context['form']
        self.assertEqual(form['deadline'].value(), datetime.date(2022, 1, 16))
        self.assertEqual(
            form['message_object'].value(),
            "Inscription UCLouvain – compléter votre dossier " f"({response.context['admission'].reference})",
        )

        first_field = form.fields.get(self.sic_free_requestable_candidate_document_with_default_file)
        self.assertIsNotNone(first_field)
        self.assertEqual(
            first_field.label,
            '<span class="fa-solid fa-link-slash"></span> My file name with default file',
        )
        self.assertEqual(first_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        second_field = form.fields.get(self.sic_free_requestable_document)
        self.assertIsNotNone(second_field)
        self.assertEqual(
            second_field.label,
            '<span class="fa-solid fa-link-slash"></span> My file name',
        )
        self.assertEqual(second_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        # Custom deadline in the second part of September
        with freezegun.freeze_time('2022-09-20'):
            self.client.force_login(user=self.second_sic_manager_user)

            response = self.client.get(url)

            self.assertEqual(response.status_code, 200)

            form = response.context['form']
            self.assertEqual(form['deadline'].value(), datetime.date(2022, 9, 30))

        # Post an invalid form -> missing fields
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('deadline', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('message_object', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('message_content', []))
        self.assertIn(gettext('At least one document must be selected.'), form.errors.get('__all__', []))

        # Post an invalid form -> invalid identifiers
        response = self.client.post(
            url,
            data={
                'deadline': '2022-01-15',
                'message_object': 'Objects',
                'message_content': 'Content',
                self.fac_free_requestable_document: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(gettext('At least one document must be selected.'), form.errors.get('__all__', []))

        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])

        # Post a valid form
        response = self.client.post(
            url,
            data={
                'deadline': '2022-01-15',
                'message_object': 'Objects',
                'message_content': 'Content',
                self.sic_free_requestable_document: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                self.sic_free_requestable_candidate_document_with_default_file: (
                    StatutReclamationEmplacementDocument.IMMEDIATEMENT.name
                ),
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        self.general_admission.refresh_from_db()

        # Check that the requested documents have been updated
        self.assertEqual(
            self.general_admission.requested_documents[self.sic_free_requestable_document],
            {
                'last_actor': self.second_sic_manager_user.person.global_id,
                'reason': 'My reason',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                'last_action_at': '2022-01-03T00:00:00',
                'status': StatutEmplacementDocument.RECLAME.name,
                'requested_at': '2022-01-03T00:00:00',
                'deadline_at': '2022-01-15',
                'automatically_required': False,
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                'related_checklist_tab': '',
            },
        )

        # Check that the proposition status has been changed
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.second_sic_manager_user.person)

        # Check that the email has been sent to the candidate
        self.assertEqual(EmailNotification.objects.count(), 1)
        email_notification: EmailNotification = EmailNotification.objects.first()
        self.assertEqual(email_notification.person, self.general_admission.candidate)
        email_object = message_from_string(email_notification.payload)
        self.assertEqual(email_object['To'], 'candidate@test.be')
        self.assertIn(form.cleaned_data['message_content'], email_notification.payload)
        self.assertIn(form.cleaned_data['message_object'], email_notification.payload)

        # Check history
        self.assertEqual(HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid).count(), 2)
        self.assertTrue(
            HistoryEntry.objects.filter(
                object_uuid=self.general_admission.uuid,
                tags=['proposition', 'message'],
            ).exists()
        )
        self.assertTrue(
            HistoryEntry.objects.filter(
                object_uuid=self.general_admission.uuid,
                tags=['proposition', 'status-changed'],
            ).exists()
        )

        frozen_time.move_to('2022-01-05')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])
        HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid).delete()

        # Cancel the documents request
        cancel_url = resolve_url(
            'admission:general-education:cancel-document-request',
            uuid=self.general_admission.uuid,
        )

        response = self.client.post(cancel_url, data={}, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.general_admission.refresh_from_db()

        # Check that the requested documents have been updated
        self.assertEqual(
            self.general_admission.requested_documents[self.sic_free_requestable_document],
            {
                'last_actor': self.second_sic_manager_user.person.global_id,
                'reason': 'My reason',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                'last_action_at': '2022-01-05T00:00:00',
                'status': StatutEmplacementDocument.RECLAMATION_ANNULEE.name,
                'requested_at': '',
                'deadline_at': '',
                'automatically_required': False,
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                'related_checklist_tab': '',
            },
        )

        # Check that the proposition status has been changed
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.CONFIRMEE.name)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.second_sic_manager_user.person)

        # Check history
        entry: Optional[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid).first()

        self.assertIsNotNone(entry)
        self.assertCountEqual(entry.tags, ['proposition', 'status-changed'])
        self.assertEqual(entry.message_fr, 'La réclamation des documents complémentaires a été annulée par SIC.')
        self.assertEqual(entry.message_en, 'The request for additional information has been cancelled by SIC.')
        self.assertEqual(
            entry.author,
            f'{self.second_sic_manager_user.person.first_name} {self.second_sic_manager_user.person.last_name}',
        )

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_document_detail_fac_manager(self, frozen_time):
        self.init_documents(for_fac=True)

        self.client.force_login(user=self.second_fac_manager_user)

        fac_free_requestable_document_without_status = self._create_a_free_document(
            self.fac_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
        )
        self.general_admission.refresh_from_db()
        self.general_admission.requested_documents[fac_free_requestable_document_without_status]['request_status'] = ''
        self.general_admission.save(update_fields=['requested_documents'])

        url = resolve_url('admission:general-education:documents', uuid=self.general_admission.uuid)

        # Get the list and the request form
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.general_admission.uuid)
        self.assertTrue(len(response.context['documents']) > 0)

        form = response.context['form']
        self.assertEqual(form['deadline'].value(), datetime.date(2022, 1, 16))
        self.assertEqual(
            form['message_object'].value(),
            "Inscription UCLouvain – compléter votre dossier " f"({response.context['admission'].reference})",
        )

        first_field = form.fields.get(self.fac_free_requestable_candidate_document_with_default_file)
        self.assertIsNotNone(first_field)
        self.assertEqual(
            first_field.label,
            '<span class="fa-solid fa-link-slash"></span> '
            '<span class="fa-solid fa-building-columns"></span> '
            'My file name with default file',
        )
        self.assertEqual(first_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        second_field = form.fields.get(self.fac_free_requestable_document)
        self.assertIsNotNone(second_field)
        self.assertEqual(
            second_field.label,
            '<span class="fa-solid fa-link-slash"></span> '
            '<span class="fa-solid fa-building-columns"></span> '
            'My file name',
        )
        self.assertEqual(second_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        # The third field should be missing as there is no request status
        third_field = form.fields.get(fac_free_requestable_document_without_status)
        self.assertIsNone(third_field)

        # Simulate that the field is not missing but still requested
        self.general_admission.refresh_from_db()
        specific_question_uuid = str(uuid.UUID(self.fac_free_requestable_document.split('.')[-1]))
        self.general_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        self.general_admission.save(update_fields=['specific_question_answers'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        form = response.context['form']

        first_field = form.fields.get(self.fac_free_requestable_candidate_document_with_default_file)
        self.assertIsNotNone(first_field)
        self.assertEqual(
            first_field.label,
            '<span class="fa-solid fa-link-slash"></span> '
            '<span class="fa-solid fa-building-columns"></span> '
            'My file name with default file',
        )
        self.assertEqual(first_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        second_field = form.fields.get(self.fac_free_requestable_document)
        self.assertIsNotNone(second_field)
        self.assertEqual(
            second_field.label,
            '<span class="fa-solid fa-paperclip"></span> '
            '<span class="fa-solid fa-building-columns"></span> '
            'My file name',
        )

        self.general_admission.specific_question_answers.pop(specific_question_uuid)
        self.general_admission.save(update_fields=['specific_question_answers'])

        # Post an invalid form -> missing fields
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('deadline', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('message_object', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('message_content', []))
        self.assertIn(gettext('At least one document must be selected.'), form.errors.get('__all__', []))

        # Post an invalid form -> invalid identifiers
        response = self.client.post(
            url,
            data={
                'deadline': '2022-01-15',
                'message_object': 'Objects',
                'message_content': 'Content',
                self.sic_free_requestable_document: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(gettext('At least one document must be selected.'), form.errors.get('__all__', []))

        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])

        # Post a valid form
        response = self.client.post(
            url,
            data={
                'deadline': '2022-01-15',
                'message_object': 'Objects',
                'message_content': 'Content',
                self.fac_free_requestable_document: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                self.fac_free_requestable_candidate_document_with_default_file: (
                    StatutReclamationEmplacementDocument.IMMEDIATEMENT.name
                ),
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        self.general_admission.refresh_from_db()

        # Check that the requested documents have been updated
        self.assertEqual(
            self.general_admission.requested_documents[self.fac_free_requestable_document],
            {
                'last_actor': self.second_fac_manager_user.person.global_id,
                'reason': 'My reason',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
                'last_action_at': '2022-01-03T00:00:00',
                'status': StatutEmplacementDocument.RECLAME.name,
                'requested_at': '2022-01-03T00:00:00',
                'deadline_at': '2022-01-15',
                'automatically_required': False,
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                'related_checklist_tab': '',
            },
        )

        # Check that the proposition status has been changed
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.second_fac_manager_user.person)

        # Check that the email has been sent to the candidate
        self.assertEqual(EmailNotification.objects.count(), 1)
        email_notification: EmailNotification = EmailNotification.objects.first()
        self.assertEqual(email_notification.person, self.general_admission.candidate)
        email_object = message_from_string(email_notification.payload)
        self.assertEqual(email_object['To'], 'candidate@test.be')
        self.assertIn(form.cleaned_data['message_content'], email_notification.payload)
        self.assertIn(form.cleaned_data['message_object'], email_notification.payload)

        # Check history
        self.assertEqual(HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid).count(), 2)
        self.assertTrue(
            HistoryEntry.objects.filter(
                object_uuid=self.general_admission.uuid,
                tags=['proposition', 'message'],
            ).exists()
        )
        self.assertTrue(
            HistoryEntry.objects.filter(
                object_uuid=self.general_admission.uuid,
                tags=['proposition', 'status-changed'],
            ).exists()
        )

        frozen_time.move_to('2022-01-05')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])
        HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid).delete()

        # Cancel the documents request
        cancel_url = resolve_url(
            'admission:general-education:cancel-document-request',
            uuid=self.general_admission.uuid,
        )

        response = self.client.post(cancel_url, data={}, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.general_admission.refresh_from_db()

        # Check that the requested documents have been updated
        self.assertEqual(
            self.general_admission.requested_documents[self.fac_free_requestable_document],
            {
                'last_actor': self.second_fac_manager_user.person.global_id,
                'reason': 'My reason',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
                'last_action_at': '2022-01-05T00:00:00',
                'status': StatutEmplacementDocument.RECLAMATION_ANNULEE.name,
                'requested_at': '',
                'deadline_at': '',
                'automatically_required': False,
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                'related_checklist_tab': '',
            },
        )

        # Check that the proposition status has been changed
        self.assertEqual(self.general_admission.status, ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.second_fac_manager_user.person)

        # Check history
        entry: Optional[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid).first()

        self.assertIsNotNone(entry)
        self.assertCountEqual(entry.tags, ['proposition', 'status-changed'])
        self.assertEqual(entry.message_fr, 'La réclamation des documents complémentaires a été annulée par FAC.')
        self.assertEqual(entry.message_en, 'The request for additional information has been cancelled by FAC.')
        self.assertEqual(
            entry.author,
            f'{self.second_fac_manager_user.person.first_name} {self.second_fac_manager_user.person.last_name}',
        )

    def test_general_document_detail_view(self):
        self.init_documents(for_sic=True)

        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:detail',
            uuid=self.general_admission.uuid,
            identifier=self.sic_free_requestable_document,
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Not filled document
        context = response.context
        self.assertEqual(context['document_identifier'], self.sic_free_requestable_document)
        self.assertEqual(context['document_type'], TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name)
        self.assertEqual(context['requestable_document'], True)
        self.assertEqual(context['editable_document'], True)
        self.assertEqual(context['request_reason'], 'My reason')

        # Check that the forms are well initialized
        self.assertEqual(context['request_form'].fields['request_status'].required, False)
        self.assertEqual(
            context['request_form']['request_status'].value(),
            StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
        )
        self.assertEqual(context['request_form']['reason'].value(), 'My reason')
        self.assertEqual(context['replace_form'].fields['file'].mimetypes, [PDF_MIME_TYPE])
        self.assertEqual(context['replace_form']['file'].value(), [])
        self.assertEqual(context['upload_form'].fields['file'].mimetypes, [PDF_MIME_TYPE])
        self.assertEqual(context['upload_form']['file'].value(), [])

        # Filled document
        file_uuid = uuid.uuid4()
        specific_question_uuid = str(uuid.UUID(self.sic_free_requestable_document.split('.')[-1]))
        self.general_admission.specific_question_answers[specific_question_uuid] = [file_uuid]
        self.general_admission.save(update_fields=['specific_question_answers'])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['document_uuid'], file_uuid)
        self.assertEqual(context['document_write_token'], 'foobar')
        self.assertEqual(context['document_metadata'], self.file_metadata)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_doctorate_document_detail_sic_manager(self, frozen_time):
        self.init_documents(for_sic=True, admission=self.doctorate_admission)

        self.client.force_login(user=self.second_sic_manager_user)

        url = resolve_url('admission:doctorate:documents', uuid=self.doctorate_admission.uuid)

        # Get the list and the request form
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.doctorate_admission.uuid)
        self.assertTrue(len(response.context['documents']) > 0)

        form = response.context['form']
        self.assertEqual(form['deadline'].value(), datetime.date(2022, 1, 16))
        self.assertEqual(
            form['message_object'].value(),
            "Inscription UCLouvain – compléter votre dossier " f"({response.context['admission'].reference})",
        )

        first_field = form.fields.get(self.sic_free_requestable_candidate_document_with_default_file)
        self.assertIsNotNone(first_field)
        self.assertEqual(
            first_field.label,
            '<span class="fa-solid fa-link-slash"></span> My file name with default file',
        )
        self.assertEqual(first_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        second_field = form.fields.get(self.sic_free_requestable_document)
        self.assertIsNotNone(second_field)
        self.assertEqual(
            second_field.label,
            '<span class="fa-solid fa-link-slash"></span> My file name',
        )
        self.assertEqual(second_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        # Custom deadline in the second part of September
        with freezegun.freeze_time('2022-09-20'):
            self.client.force_login(user=self.second_sic_manager_user)

            response = self.client.get(url)

            self.assertEqual(response.status_code, 200)

            form = response.context['form']
            self.assertEqual(form['deadline'].value(), datetime.date(2022, 9, 30))

        # Post an invalid form -> missing fields
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('deadline', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('message_object', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('message_content', []))
        self.assertIn(gettext('At least one document must be selected.'), form.errors.get('__all__', []))

        # Post an invalid form -> invalid identifiers
        response = self.client.post(
            url,
            data={
                'deadline': '2022-01-15',
                'message_object': 'Objects',
                'message_content': 'Content',
                self.sic_free_non_requestable_internal_document: (
                    StatutReclamationEmplacementDocument.IMMEDIATEMENT.name
                ),
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(gettext('At least one document must be selected.'), form.errors.get('__all__', []))

        frozen_time.move_to('2022-01-03')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['last_update_author'])

        # Post a valid form
        response = self.client.post(
            url,
            data={
                'deadline': '2022-01-15',
                'message_object': 'Objects',
                'message_content': 'Content',
                self.sic_free_requestable_document: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                self.sic_free_requestable_candidate_document_with_default_file: (
                    StatutReclamationEmplacementDocument.IMMEDIATEMENT.name
                ),
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        self.doctorate_admission.refresh_from_db()

        # Check that the requested documents have been updated
        self.assertEqual(
            self.doctorate_admission.requested_documents[self.sic_free_requestable_document],
            {
                'last_actor': self.second_sic_manager_user.person.global_id,
                'reason': 'My reason',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                'last_action_at': '2022-01-03T00:00:00',
                'status': StatutEmplacementDocument.RECLAME.name,
                'requested_at': '2022-01-03T00:00:00',
                'deadline_at': '2022-01-15',
                'automatically_required': False,
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                'related_checklist_tab': '',
            },
        )

        # Check that the proposition status has been changed
        self.assertEqual(self.doctorate_admission.status, ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_SIC.name)

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.second_sic_manager_user.person)

        # Check that the email has been sent to the candidate
        self.assertEqual(EmailNotification.objects.count(), 1)
        email_notification: EmailNotification = EmailNotification.objects.first()
        self.assertEqual(email_notification.person, self.doctorate_admission.candidate)
        email_object = message_from_string(email_notification.payload)
        self.assertEqual(email_object['To'], 'candidate@test.be')
        self.assertIn(form.cleaned_data['message_content'], email_notification.payload)
        self.assertIn(form.cleaned_data['message_object'], email_notification.payload)

        # Check history
        self.assertEqual(HistoryEntry.objects.filter(object_uuid=self.doctorate_admission.uuid).count(), 2)
        self.assertTrue(
            HistoryEntry.objects.filter(
                object_uuid=self.doctorate_admission.uuid,
                tags=['proposition', 'message'],
            ).exists()
        )
        self.assertTrue(
            HistoryEntry.objects.filter(
                object_uuid=self.doctorate_admission.uuid,
                tags=['proposition', 'status-changed'],
            ).exists()
        )

        frozen_time.move_to('2022-01-05')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['last_update_author'])
        HistoryEntry.objects.filter(object_uuid=self.doctorate_admission.uuid).delete()

        # Cancel the documents request
        cancel_url = resolve_url(
            'admission:doctorate:cancel-document-request',
            uuid=self.doctorate_admission.uuid,
        )

        response = self.client.post(cancel_url, data={}, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.doctorate_admission.refresh_from_db()

        # Check that the requested documents have been updated
        self.assertEqual(
            self.doctorate_admission.requested_documents[self.sic_free_requestable_document],
            {
                'last_actor': self.second_sic_manager_user.person.global_id,
                'reason': 'My reason',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                'last_action_at': '2022-01-05T00:00:00',
                'status': StatutEmplacementDocument.RECLAMATION_ANNULEE.name,
                'requested_at': '',
                'deadline_at': '',
                'automatically_required': False,
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                'related_checklist_tab': '',
            },
        )

        # Check that the proposition status has been changed
        self.assertEqual(self.doctorate_admission.status, ChoixStatutPropositionDoctorale.CONFIRMEE.name)

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.second_sic_manager_user.person)

        # Check history
        entry: Optional[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.doctorate_admission.uuid).first()

        self.assertIsNotNone(entry)
        self.assertCountEqual(entry.tags, ['proposition', 'status-changed'])
        self.assertEqual(entry.message_fr, 'La réclamation des documents complémentaires a été annulée par SIC.')
        self.assertEqual(entry.message_en, 'The request for additional information has been cancelled by SIC.')
        self.assertEqual(
            entry.author,
            f'{self.second_sic_manager_user.person.first_name} {self.second_sic_manager_user.person.last_name}',
        )

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_doctorate_document_detail_fac_manager(self, frozen_time):
        self.init_documents(for_fac=True, admission=self.doctorate_admission)

        self.client.force_login(user=self.second_doctorate_fac_manager_user)

        fac_free_requestable_document_without_status = self._create_a_free_document(
            self.doctorate_fac_manager_user,
            TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
            admission=self.doctorate_admission,
        )
        self.doctorate_admission.refresh_from_db()
        self.doctorate_admission.requested_documents[fac_free_requestable_document_without_status][
            'request_status'
        ] = ''
        self.doctorate_admission.save(update_fields=['requested_documents'])

        url = resolve_url('admission:doctorate:documents', uuid=self.doctorate_admission.uuid)

        # Get the list and the request form
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admission'].uuid, self.doctorate_admission.uuid)
        self.assertTrue(len(response.context['documents']) > 0)

        form = response.context['form']
        self.assertEqual(form['deadline'].value(), datetime.date(2022, 1, 16))
        self.assertEqual(
            form['message_object'].value(),
            "Inscription UCLouvain – compléter votre dossier " f"({response.context['admission'].reference})",
        )

        first_field = form.fields.get(self.fac_free_requestable_candidate_document_with_default_file)
        self.assertIsNotNone(first_field)
        self.assertEqual(
            first_field.label,
            '<span class="fa-solid fa-link-slash"></span> '
            '<span class="fa-solid fa-building-columns"></span> '
            'My file name with default file',
        )
        self.assertEqual(first_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        second_field = form.fields.get(self.fac_free_requestable_document)
        self.assertIsNotNone(second_field)
        self.assertEqual(
            second_field.label,
            '<span class="fa-solid fa-link-slash"></span> '
            '<span class="fa-solid fa-building-columns"></span> '
            'My file name',
        )
        self.assertEqual(second_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        # The third field should be missing as there is no request status
        third_field = form.fields.get(fac_free_requestable_document_without_status)
        self.assertIsNone(third_field)

        # Simulate that the field is not missing but still requested
        self.doctorate_admission.refresh_from_db()
        specific_question_uuid = str(uuid.UUID(self.fac_free_requestable_document.split('.')[-1]))
        self.doctorate_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        self.doctorate_admission.save(update_fields=['specific_question_answers'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        form = response.context['form']

        first_field = form.fields.get(self.fac_free_requestable_candidate_document_with_default_file)
        self.assertIsNotNone(first_field)
        self.assertEqual(
            first_field.label,
            '<span class="fa-solid fa-link-slash"></span> '
            '<span class="fa-solid fa-building-columns"></span> '
            'My file name with default file',
        )
        self.assertEqual(first_field.initial, StatutReclamationEmplacementDocument.IMMEDIATEMENT.name)

        second_field = form.fields.get(self.fac_free_requestable_document)
        self.assertIsNotNone(second_field)
        self.assertEqual(
            second_field.label,
            '<span class="fa-solid fa-paperclip"></span> '
            '<span class="fa-solid fa-building-columns"></span> '
            'My file name',
        )

        self.doctorate_admission.specific_question_answers.pop(specific_question_uuid)
        self.doctorate_admission.save(update_fields=['specific_question_answers'])

        # Post an invalid form -> missing fields
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('deadline', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('message_object', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('message_content', []))
        self.assertIn(gettext('At least one document must be selected.'), form.errors.get('__all__', []))

        # Post an invalid form -> invalid identifiers
        response = self.client.post(
            url,
            data={
                'deadline': '2022-01-15',
                'message_object': 'Objects',
                'message_content': 'Content',
                self.fac_free_non_requestable_internal_document: (
                    StatutReclamationEmplacementDocument.IMMEDIATEMENT.name
                ),
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(gettext('At least one document must be selected.'), form.errors.get('__all__', []))

        frozen_time.move_to('2022-01-03')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['last_update_author'])

        # Post a valid form
        response = self.client.post(
            url,
            data={
                'deadline': '2022-01-15',
                'message_object': 'Objects',
                'message_content': 'Content',
                self.fac_free_requestable_document: StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                self.fac_free_requestable_candidate_document_with_default_file: (
                    StatutReclamationEmplacementDocument.IMMEDIATEMENT.name
                ),
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_valid())

        self.doctorate_admission.refresh_from_db()

        # Check that the requested documents have been updated
        self.assertEqual(
            self.doctorate_admission.requested_documents[self.fac_free_requestable_document],
            {
                'last_actor': self.second_doctorate_fac_manager_user.person.global_id,
                'reason': 'My reason',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
                'last_action_at': '2022-01-03T00:00:00',
                'status': StatutEmplacementDocument.RECLAME.name,
                'requested_at': '2022-01-03T00:00:00',
                'deadline_at': '2022-01-15',
                'automatically_required': False,
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                'related_checklist_tab': '',
            },
        )

        # Check that the proposition status has been changed
        self.assertEqual(self.doctorate_admission.status, ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name)

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.second_doctorate_fac_manager_user.person)

        # Check that the email has been sent to the candidate
        self.assertEqual(EmailNotification.objects.count(), 1)
        email_notification: EmailNotification = EmailNotification.objects.first()
        self.assertEqual(email_notification.person, self.doctorate_admission.candidate)
        email_object = message_from_string(email_notification.payload)
        self.assertEqual(email_object['To'], 'candidate@test.be')
        self.assertIn(form.cleaned_data['message_content'], email_notification.payload)
        self.assertIn(form.cleaned_data['message_object'], email_notification.payload)

        # Check history
        self.assertEqual(HistoryEntry.objects.filter(object_uuid=self.doctorate_admission.uuid).count(), 2)
        self.assertTrue(
            HistoryEntry.objects.filter(
                object_uuid=self.doctorate_admission.uuid,
                tags=['proposition', 'message'],
            ).exists()
        )
        self.assertTrue(
            HistoryEntry.objects.filter(
                object_uuid=self.doctorate_admission.uuid,
                tags=['proposition', 'status-changed'],
            ).exists()
        )

        frozen_time.move_to('2022-01-05')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['last_update_author'])
        HistoryEntry.objects.filter(object_uuid=self.doctorate_admission.uuid).delete()

        # Cancel the documents request
        cancel_url = resolve_url(
            'admission:doctorate:cancel-document-request',
            uuid=self.doctorate_admission.uuid,
        )

        response = self.client.post(cancel_url, data={}, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.doctorate_admission.refresh_from_db()

        # Check that the requested documents have been updated
        self.assertEqual(
            self.doctorate_admission.requested_documents[self.fac_free_requestable_document],
            {
                'last_actor': self.second_doctorate_fac_manager_user.person.global_id,
                'reason': 'My reason',
                'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
                'last_action_at': '2022-01-05T00:00:00',
                'status': StatutEmplacementDocument.RECLAMATION_ANNULEE.name,
                'requested_at': '',
                'deadline_at': '',
                'automatically_required': False,
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
                'related_checklist_tab': '',
            },
        )

        # Check that the proposition status has been changed
        self.assertEqual(self.doctorate_admission.status, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name)

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.second_doctorate_fac_manager_user.person)

        # Check history
        entry: Optional[HistoryEntry] = HistoryEntry.objects.filter(object_uuid=self.doctorate_admission.uuid).first()

        self.assertIsNotNone(entry)
        self.assertCountEqual(entry.tags, ['proposition', 'status-changed'])
        self.assertEqual(entry.message_fr, 'La réclamation des documents complémentaires a été annulée par FAC.')
        self.assertEqual(entry.message_en, 'The request for additional information has been cancelled by FAC.')
        self.assertEqual(
            entry.author,
            f'{self.second_doctorate_fac_manager_user.person.first_name} {self.second_doctorate_fac_manager_user.person.last_name}',
        )

    def test_doctorate_document_detail_view(self):
        self.init_documents(for_sic=True, admission=self.doctorate_admission)

        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:doctorate:document:detail',
            uuid=self.doctorate_admission.uuid,
            identifier=self.sic_free_requestable_document,
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Not filled document
        context = response.context
        self.assertEqual(context['document_identifier'], self.sic_free_requestable_document)
        self.assertEqual(context['document_type'], TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name)
        self.assertEqual(context['requestable_document'], True)
        self.assertEqual(context['editable_document'], True)
        self.assertEqual(context['request_reason'], 'My reason')

        # Check that the forms are well initialized
        self.assertEqual(context['request_form'].fields['request_status'].required, False)
        self.assertEqual(
            context['request_form']['request_status'].value(),
            StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
        )
        self.assertEqual(context['request_form']['reason'].value(), 'My reason')
        self.assertEqual(context['replace_form'].fields['file'].mimetypes, [PDF_MIME_TYPE])
        self.assertEqual(context['replace_form']['file'].value(), [])
        self.assertEqual(context['upload_form'].fields['file'].mimetypes, [PDF_MIME_TYPE])
        self.assertEqual(context['upload_form']['file'].value(), [])

        # Filled document
        file_uuid = uuid.uuid4()
        specific_question_uuid = str(uuid.UUID(self.sic_free_requestable_document.split('.')[-1]))
        self.doctorate_admission.specific_question_answers[specific_question_uuid] = [file_uuid]
        self.doctorate_admission.save(update_fields=['specific_question_answers'])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['document_uuid'], file_uuid)
        self.assertEqual(context['document_write_token'], 'foobar')
        self.assertEqual(context['document_metadata'], self.file_metadata)
