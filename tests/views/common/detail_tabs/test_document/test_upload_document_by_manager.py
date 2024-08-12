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

import freezegun
from django.shortcuts import resolve_url
from django.test import override_settings

from admission.constants import IMAGE_MIME_TYPES
from admission.ddd.admission.enums.emplacement_document import (
    IdentifiantBaseEmplacementDocument,
    OngletsDemande,
)
from admission.tests.views.common.detail_tabs.test_document import BaseDocumentViewTestCase
from base.forms.utils.file_field import PDF_MIME_TYPE
from osis_document.contrib.forms import FileUploadField


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class UploadDocumentByManagerTestCase(BaseDocumentViewTestCase):
    # The manager uploads the document
    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_sic_manager_uploads_a_document(self, frozen_time):
        self.init_documents(for_sic=True)

        base_url = 'admission:general-education:document:upload'

        self.client.force_login(user=self.sic_manager_user)

        # Unknown document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A SIC manager cannot upload FAC documents
            self.fac_free_non_requestable_internal_document,
            self.fac_free_requestable_candidate_document_with_default_file,
            self.fac_free_requestable_document,
            # Or system ones
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.general_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        # A SIC manager can upload SIC documents
        # Internal document
        self.change_remote_metadata_patcher.reset_mock()
        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])
        self.general_admission.refresh_from_db()
        old_document_uuid = uuid.UUID(self.sic_free_non_requestable_internal_document.split('.')[-1])
        self.assertIn(old_document_uuid, self.general_admission.uclouvain_sic_documents)
        self.assertEqual(len(self.general_admission.uclouvain_sic_documents), 1)
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.sic_free_non_requestable_internal_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.general_admission.refresh_from_db()
        self.assertNotIn(old_document_uuid, self.general_admission.uclouvain_sic_documents)
        self.assertEqual(len(self.general_admission.uclouvain_sic_documents), 1)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Requestable document
        self.change_remote_metadata_patcher.reset_mock()
        specific_question_uuid = str(uuid.UUID(self.sic_free_requestable_document.split('.')[-1]))
        self.general_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        frozen_time.move_to('2022-01-04')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['specific_question_answers', 'last_update_author'])

        old_document_uuid = self.general_admission.requested_documents.get(self.sic_free_requestable_document)
        self.assertIsNotNone(old_document_uuid)

        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.sic_free_requestable_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.general_admission.refresh_from_db()
        self.assertNotEqual(
            self.general_admission.specific_question_answers.get(specific_question_uuid),
            old_document_uuid,
        )
        self.assertEqual(len(self.general_admission.specific_question_answers.get(specific_question_uuid)), 1)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
            },
        )

        # Non free document
        self.change_remote_metadata_patcher.reset_mock()
        old_document_uuid = [uuid.uuid4()]
        self.general_admission.curriculum = old_document_uuid
        frozen_time.move_to('2022-01-05')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['curriculum', 'last_update_author'])

        # Get the form with the right configuration depending on the document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(form.fields['file'].max_files, 1)
        self.assertEqual(form.fields['file'].min_files, 1)
        self.assertCountEqual(form.fields['file'].mimetypes, [PDF_MIME_TYPE])

        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertCountEqual(form.fields['file'].mimetypes, list(IMAGE_MIME_TYPES))

        # Post an invalid form -> at least one file must be specified
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(FileUploadField.default_error_messages['min_files'], form.errors.get('file', []))

        # Post an invalid form -> only one file must be specified
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'file_0': ['file_0-token'],
                'file_1': ['file_1-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertIn(FileUploadField.default_error_messages['max_files'], form.errors.get('file', []))

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.general_admission.refresh_from_db()
        self.assertNotEqual(self.general_admission.curriculum, old_document_uuid)
        self.assertEqual(len(self.general_admission.curriculum), 1)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
            },
        )

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_general_fac_manager_uploads_a_document(self, frozen_time):
        self.init_documents(for_fac=True)

        base_url = 'admission:general-education:document:upload'

        self.client.force_login(user=self.fac_manager_user)

        # Unknown document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A FAC manager cannot upload SIC documents
            self.sic_free_non_requestable_internal_document,
            self.sic_free_requestable_candidate_document_with_default_file,
            self.sic_free_requestable_document,
            # Or system ones
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.general_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        # A FAC manager can upload FAC documents
        # Internal document
        self.change_remote_metadata_patcher.reset_mock()
        frozen_time.move_to('2022-01-03')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['last_update_author'])
        self.general_admission.refresh_from_db()
        old_document_uuid = uuid.UUID(self.fac_free_non_requestable_internal_document.split('.')[-1])
        self.assertIn(old_document_uuid, self.general_admission.uclouvain_fac_documents)
        self.assertEqual(len(self.general_admission.uclouvain_fac_documents), 1)
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.fac_free_non_requestable_internal_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        # Check last modification data
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(old_document_uuid, self.general_admission.uclouvain_fac_documents)
        self.assertEqual(len(self.general_admission.uclouvain_fac_documents), 1)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.fac_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.fac_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Requestable document
        self.change_remote_metadata_patcher.reset_mock()
        specific_question_uuid = str(uuid.UUID(self.fac_free_requestable_document.split('.')[-1]))
        self.general_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        frozen_time.move_to('2022-01-04')
        self.general_admission.last_update_author = None
        self.general_admission.save(update_fields=['specific_question_answers', 'last_update_author'])

        old_document_uuid = self.general_admission.requested_documents.get(self.fac_free_requestable_document)
        self.assertIsNotNone(old_document_uuid)

        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.fac_free_requestable_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.general_admission.refresh_from_db()
        self.assertNotEqual(
            self.general_admission.specific_question_answers.get(specific_question_uuid),
            old_document_uuid,
        )
        self.assertEqual(len(self.general_admission.specific_question_answers.get(specific_question_uuid)), 1)

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.fac_manager_user.person.global_id,
            },
        )

        # Replace a non free document is not allowed for a FAC manager
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.general_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 403)

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_continuing_sic_manager_uploads_a_document(self, frozen_time):
        self.init_documents(for_sic=True, admission=self.continuing_admission)

        base_url = 'admission:continuing-education:document:upload'

        self.client.force_login(user=self.sic_manager_user)

        # Unknown document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.continuing_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A SIC manager cannot upload system documents
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.continuing_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        # A SIC manager can upload SIC and FAC documents
        for identifier in [
            self.sic_free_requestable_candidate_document_with_default_file,
            self.sic_free_requestable_document,
            self.fac_free_non_requestable_internal_document,
            self.fac_free_requestable_candidate_document_with_default_file,
            self.fac_free_requestable_document,
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.continuing_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 200)

        # Non free document
        self.change_remote_metadata_patcher.reset_mock()
        old_document_uuid = [uuid.uuid4()]
        self.continuing_admission.curriculum = old_document_uuid
        frozen_time.move_to('2022-01-05')
        self.continuing_admission.last_update_author = None
        self.continuing_admission.save(update_fields=['curriculum', 'last_update_author'])

        # Get the form with the right configuration depending on the document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.continuing_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(form.fields['file'].max_files, 1)
        self.assertEqual(form.fields['file'].min_files, 1)
        self.assertCountEqual(form.fields['file'].mimetypes, [PDF_MIME_TYPE])

        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.continuing_admission.uuid,
                identifier=f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertCountEqual(form.fields['file'].mimetypes, list(IMAGE_MIME_TYPES))

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.continuing_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.continuing_admission.refresh_from_db()
        self.assertNotEqual(self.continuing_admission.curriculum, old_document_uuid)
        self.assertEqual(len(self.continuing_admission.curriculum), 1)

        # Check last modification data
        self.assertEqual(self.continuing_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.continuing_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
            },
        )

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_continuing_fac_manager_uploads_a_document(self, frozen_time):
        self.init_documents(for_fac=True, admission=self.continuing_admission)

        base_url = 'admission:continuing-education:document:upload'

        self.client.force_login(user=self.continuing_fac_manager_user)

        # Unknown document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.continuing_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A FAC manager cannot upload system documents
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.continuing_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        # A FAC manager can upload SIC and FAC documents
        for identifier in [
            self.sic_free_requestable_candidate_document_with_default_file,
            self.sic_free_requestable_document,
            self.fac_free_non_requestable_internal_document,
            self.fac_free_requestable_candidate_document_with_default_file,
            self.fac_free_requestable_document,
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.continuing_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 200)

        # Non free document
        self.change_remote_metadata_patcher.reset_mock()
        old_document_uuid = [uuid.uuid4()]
        self.continuing_admission.curriculum = old_document_uuid
        frozen_time.move_to('2022-01-05')
        self.continuing_admission.last_update_author = None
        self.continuing_admission.save(update_fields=['curriculum', 'last_update_author'])

        # Get the form with the right configuration depending on the document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.continuing_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(form.fields['file'].max_files, 1)
        self.assertEqual(form.fields['file'].min_files, 1)
        self.assertCountEqual(form.fields['file'].mimetypes, [PDF_MIME_TYPE])

        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.continuing_admission.uuid,
                identifier=f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertCountEqual(form.fields['file'].mimetypes, list(IMAGE_MIME_TYPES))

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.continuing_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.continuing_admission.refresh_from_db()
        self.assertNotEqual(self.continuing_admission.curriculum, old_document_uuid)
        self.assertEqual(len(self.continuing_admission.curriculum), 1)

        # Check last modification data
        self.assertEqual(self.continuing_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.continuing_admission.last_update_author, self.continuing_fac_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.continuing_fac_manager_user.person.global_id,
            },
        )

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_doctorate_sic_manager_uploads_a_document(self, frozen_time):
        self.init_documents(for_sic=True, admission=self.doctorate_admission)

        base_url = 'admission:doctorate:document:upload'

        self.client.force_login(user=self.sic_manager_user)

        # Unknown document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A SIC manager cannot upload system documents
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.doctorate_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        for identifier in [
            # A SIC manager can upload FAC documents
            self.fac_free_non_requestable_internal_document,
            self.fac_free_requestable_candidate_document_with_default_file,
            self.fac_free_requestable_document,
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.doctorate_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 200)

        # A SIC manager can upload SIC documents
        # Internal document
        self.change_remote_metadata_patcher.reset_mock()
        frozen_time.move_to('2022-01-03')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['last_update_author'])
        self.doctorate_admission.refresh_from_db()
        old_document_uuid = uuid.UUID(self.sic_free_non_requestable_internal_document.split('.')[-1])
        self.assertIn(old_document_uuid, self.doctorate_admission.uclouvain_sic_documents)
        self.assertEqual(len(self.doctorate_admission.uclouvain_sic_documents), 1)
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.sic_free_non_requestable_internal_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.doctorate_admission.refresh_from_db()
        self.assertNotIn(old_document_uuid, self.doctorate_admission.uclouvain_sic_documents)
        self.assertEqual(len(self.doctorate_admission.uclouvain_sic_documents), 1)

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Requestable document
        self.change_remote_metadata_patcher.reset_mock()
        specific_question_uuid = str(uuid.UUID(self.sic_free_requestable_document.split('.')[-1]))
        self.doctorate_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        frozen_time.move_to('2022-01-04')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['specific_question_answers', 'last_update_author'])

        old_document_uuid = self.doctorate_admission.requested_documents.get(self.sic_free_requestable_document)
        self.assertIsNotNone(old_document_uuid)

        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.sic_free_requestable_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.doctorate_admission.refresh_from_db()
        self.assertNotEqual(
            self.doctorate_admission.specific_question_answers.get(specific_question_uuid),
            old_document_uuid,
        )
        self.assertEqual(len(self.doctorate_admission.specific_question_answers.get(specific_question_uuid)), 1)

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
            },
        )

        # Non free document
        self.change_remote_metadata_patcher.reset_mock()
        old_document_uuid = [uuid.uuid4()]
        self.doctorate_admission.curriculum = old_document_uuid
        frozen_time.move_to('2022-01-05')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['curriculum', 'last_update_author'])

        # Get the form with the right configuration depending on the document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(form.fields['file'].max_files, 1)
        self.assertEqual(form.fields['file'].min_files, 1)
        self.assertCountEqual(form.fields['file'].mimetypes, [PDF_MIME_TYPE])

        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertCountEqual(form.fields['file'].mimetypes, list(IMAGE_MIME_TYPES))

        # Post an invalid form -> at least one file must be specified
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(FileUploadField.default_error_messages['min_files'], form.errors.get('file', []))

        # Post an invalid form -> only one file must be specified
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'file_0': ['file_0-token'],
                'file_1': ['file_1-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertIn(FileUploadField.default_error_messages['max_files'], form.errors.get('file', []))

        # Post a valid form
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.doctorate_admission.refresh_from_db()
        self.assertNotEqual(self.doctorate_admission.curriculum, old_document_uuid)
        self.assertEqual(len(self.doctorate_admission.curriculum), 1)

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
            },
        )

    @freezegun.freeze_time('2022-01-01', as_kwarg='frozen_time')
    def test_doctorate_fac_manager_uploads_a_document(self, frozen_time):
        self.init_documents(for_fac=True, admission=self.doctorate_admission)

        base_url = 'admission:doctorate:document:upload'

        self.client.force_login(user=self.doctorate_fac_manager_user)

        # Unknown document
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier='unknown',
            ),
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 404)

        for identifier in [
            # A FAC manager cannot upload system documents
            f'{IdentifiantBaseEmplacementDocument.SYSTEME.name}.DOSSIER_ANALYSE',
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.doctorate_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 403)

        for identifier in [
            # A FAC manager can upload SIC documents
            self.sic_free_non_requestable_internal_document,
            self.sic_free_requestable_candidate_document_with_default_file,
            self.sic_free_requestable_document,
        ]:
            response = self.client.post(
                resolve_url(
                    base_url,
                    uuid=self.doctorate_admission.uuid,
                    identifier=identifier,
                ),
                **self.default_headers,
            )
            self.assertEqual(response.status_code, 200)

        # A FAC manager can upload FAC documents
        # Internal document
        self.change_remote_metadata_patcher.reset_mock()
        frozen_time.move_to('2022-01-03')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['last_update_author'])
        self.doctorate_admission.refresh_from_db()
        old_document_uuid = uuid.UUID(self.fac_free_non_requestable_internal_document.split('.')[-1])
        self.assertIn(old_document_uuid, self.doctorate_admission.uclouvain_fac_documents)
        self.assertEqual(len(self.doctorate_admission.uclouvain_fac_documents), 1)
        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.fac_free_non_requestable_internal_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        # Check last modification data
        self.doctorate_admission.refresh_from_db()
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.doctorate_fac_manager_user.person)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(old_document_uuid, self.doctorate_admission.uclouvain_fac_documents)
        self.assertEqual(len(self.doctorate_admission.uclouvain_fac_documents), 1)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.doctorate_fac_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.doctorate_fac_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

        # Requestable document
        self.change_remote_metadata_patcher.reset_mock()
        specific_question_uuid = str(uuid.UUID(self.fac_free_requestable_document.split('.')[-1]))
        self.doctorate_admission.specific_question_answers[specific_question_uuid] = [uuid.uuid4()]
        frozen_time.move_to('2022-01-04')
        self.doctorate_admission.last_update_author = None
        self.doctorate_admission.save(update_fields=['specific_question_answers', 'last_update_author'])

        old_document_uuid = self.doctorate_admission.requested_documents.get(self.fac_free_requestable_document)
        self.assertIsNotNone(old_document_uuid)

        response = self.client.post(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.fac_free_requestable_document,
            ),
            data={
                'file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.doctorate_admission.refresh_from_db()
        self.assertNotEqual(
            self.doctorate_admission.specific_question_answers.get(specific_question_uuid),
            old_document_uuid,
        )
        self.assertEqual(len(self.doctorate_admission.specific_question_answers.get(specific_question_uuid)), 1)

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.doctorate_fac_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.doctorate_fac_manager_user.person.global_id,
            },
        )

        # Replace a non free document is not allowed for a FAC manager
        response = self.client.get(
            resolve_url(
                base_url,
                uuid=self.doctorate_admission.uuid,
                identifier=self.non_free_document_identifier,
            ),
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
