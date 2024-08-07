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

import freezegun
from django.shortcuts import resolve_url
from django.test import override_settings

from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.tests.factories.categorized_free_document import CategorizedFreeDocumentFactory
from admission.tests.views.common.detail_tabs.test_document import BaseDocumentViewTestCase
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.forms.utils.file_field import MaxOneFileUploadField


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DocumentViewTestCase(BaseDocumentViewTestCase):
    # The manager uploads a free document that only the other managers can view
    @freezegun.freeze_time('2022-01-01')
    def test_general_sic_manager_uploads_free_and_readonly_internal_document(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-internal-upload',
            uuid=self.general_admission.uuid,
        )

        # Retrieve the empty form
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form
        # Empty data
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))
        self.assertIn(
            MaxOneFileUploadField.default_error_messages['min_files'],
            response.context['form'].errors.get('file', []),
        )

        # Too much files
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_0': ['file_0-token'],
                'upload-free-internal-document-form-file_1': ['file_1-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            MaxOneFileUploadField.default_error_messages['max_files'],
            response.context['form'].errors.get('file', []),
        )

        categorized_document = CategorizedFreeDocumentFactory(
            checklist_tab='',
            with_academic_year=True,
        )
        # Invalid categorized document because the academic year has not been selected
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_name': 'My file name',
                'upload-free-internal-document-form-file_0': ['file_0-token'],
                'upload-free-internal-document-form-document_type': categorized_document.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('academic_year', []))

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_name': 'My file name',
                'upload-free-internal-document-form-file_0': ['file_0-token'],
                'upload-free-internal-document-form-document_type': categorized_document.pk,
                'upload-free-internal-document-form-academic_year': '2018-2019',
            },
            **self.default_headers,
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].data, {})

        # Save the file into the admission
        self.general_admission.refresh_from_db()
        self.assertNotEqual(self.general_admission.uclouvain_sic_documents, [])
        self.assertEqual(self.general_admission.uclouvain_fac_documents, [])

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': categorized_document.long_label_fr,
            },
        )

    @freezegun.freeze_time('2022-01-01')
    def test_general_fac_manager_uploads_free_and_readonly_internal_document(self):
        self.general_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.general_admission.save(update_fields=['status'])

        self.client.force_login(user=self.fac_manager_user)

        url = resolve_url(
            'admission:general-education:document:free-internal-upload',
            uuid=self.general_admission.uuid,
        )

        # Retrieve the empty form
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form
        # Empty data
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))
        self.assertIn(
            MaxOneFileUploadField.default_error_messages['min_files'],
            response.context['form'].errors.get('file', []),
        )

        # Too much files
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_0': ['file_0-token'],
                'upload-free-internal-document-form-file_1': ['file_1-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            MaxOneFileUploadField.default_error_messages['max_files'],
            response.context['form'].errors.get('file', []),
        )

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_name': 'My file name',
                'upload-free-internal-document-form-file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].data, {})

        # Save the file into the admission
        self.general_admission.refresh_from_db()
        self.assertNotEqual(self.general_admission.uclouvain_fac_documents, [])
        self.assertEqual(self.general_admission.uclouvain_sic_documents, [])

        # Check last modification data
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.fac_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.fac_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

    @freezegun.freeze_time('2022-01-01')
    def test_continuing_sic_manager_uploads_free_and_readonly_internal_document(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:continuing-education:document:free-internal-upload',
            uuid=self.continuing_admission.uuid,
        )

        # Retrieve the empty form
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form
        # Empty data
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))
        self.assertIn(
            MaxOneFileUploadField.default_error_messages['min_files'],
            response.context['form'].errors.get('file', []),
        )

        # Too much files
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_0': ['file_0-token'],
                'upload-free-internal-document-form-file_1': ['file_1-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            MaxOneFileUploadField.default_error_messages['max_files'],
            response.context['form'].errors.get('file', []),
        )

        categorized_document = CategorizedFreeDocumentFactory(
            checklist_tab='',
            with_academic_year=True,
        )
        # Invalid categorized document because the academic year has not been selected
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_name': 'My file name',
                'upload-free-internal-document-form-file_0': ['file_0-token'],
                'upload-free-internal-document-form-document_type': categorized_document.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('academic_year', []))

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_name': 'My file name',
                'upload-free-internal-document-form-file_0': ['file_0-token'],
                'upload-free-internal-document-form-document_type': categorized_document.pk,
                'upload-free-internal-document-form-academic_year': '2018-2019',
            },
            **self.default_headers,
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].data, {})

        # Save the file into the admission
        self.continuing_admission.refresh_from_db()
        self.assertEqual(self.continuing_admission.uclouvain_sic_documents, [])
        self.assertNotEqual(self.continuing_admission.uclouvain_fac_documents, [])

        # Check last modification data
        self.assertEqual(self.continuing_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.continuing_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': categorized_document.long_label_fr,
            },
        )

    @freezegun.freeze_time('2022-01-01')
    def test_continuing_fac_manager_uploads_free_and_readonly_internal_document(self):
        self.continuing_admission.status = ChoixStatutPropositionContinue.CONFIRMEE.name
        self.continuing_admission.save(update_fields=['status'])

        self.client.force_login(user=self.continuing_fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:document:free-internal-upload',
            uuid=self.continuing_admission.uuid,
        )

        # Retrieve the empty form
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form
        # Empty data
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))
        self.assertIn(
            MaxOneFileUploadField.default_error_messages['min_files'],
            response.context['form'].errors.get('file', []),
        )

        # Too much files
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_0': ['file_0-token'],
                'upload-free-internal-document-form-file_1': ['file_1-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            MaxOneFileUploadField.default_error_messages['max_files'],
            response.context['form'].errors.get('file', []),
        )

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_name': 'My file name',
                'upload-free-internal-document-form-file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].data, {})

        # Save the file into the admission
        self.continuing_admission.refresh_from_db()
        self.assertNotEqual(self.continuing_admission.uclouvain_fac_documents, [])
        self.assertEqual(self.continuing_admission.uclouvain_sic_documents, [])

        # Check last modification data
        self.assertEqual(self.continuing_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.continuing_admission.last_update_author, self.continuing_fac_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.continuing_fac_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )

    @freezegun.freeze_time('2022-01-01')
    def test_doctorate_sic_manager_uploads_free_and_readonly_internal_document(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:doctorate:document:free-internal-upload',
            uuid=self.doctorate_admission.uuid,
        )

        # Retrieve the empty form
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form
        # Empty data
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))
        self.assertIn(
            MaxOneFileUploadField.default_error_messages['min_files'],
            response.context['form'].errors.get('file', []),
        )

        # Too much files
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_0': ['file_0-token'],
                'upload-free-internal-document-form-file_1': ['file_1-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            MaxOneFileUploadField.default_error_messages['max_files'],
            response.context['form'].errors.get('file', []),
        )

        categorized_document = CategorizedFreeDocumentFactory(
            checklist_tab='',
            with_academic_year=True,
        )
        # Invalid categorized document because the academic year has not been selected
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_name': 'My file name',
                'upload-free-internal-document-form-file_0': ['file_0-token'],
                'upload-free-internal-document-form-document_type': categorized_document.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('academic_year', []))

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_name': 'My file name',
                'upload-free-internal-document-form-file_0': ['file_0-token'],
                'upload-free-internal-document-form-document_type': categorized_document.pk,
                'upload-free-internal-document-form-academic_year': '2018-2019',
            },
            **self.default_headers,
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].data, {})

        # Save the file into the admission
        self.doctorate_admission.refresh_from_db()
        self.assertNotEqual(self.doctorate_admission.uclouvain_sic_documents, [])
        self.assertEqual(self.doctorate_admission.uclouvain_fac_documents, [])

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': categorized_document.long_label_fr,
            },
        )

    @freezegun.freeze_time('2022-01-01')
    def test_doctorate_fac_manager_uploads_free_and_readonly_internal_document(self):
        self.doctorate_admission.status = ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name
        self.doctorate_admission.save(update_fields=['status'])

        self.client.force_login(user=self.doctorate_fac_manager_user)

        url = resolve_url(
            'admission:doctorate:document:free-internal-upload',
            uuid=self.doctorate_admission.uuid,
        )

        # Retrieve the empty form
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        # Submit an invalid form
        # Empty data
        response = self.client.post(
            url,
            data={},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(FIELD_REQUIRED_MESSAGE, response.context['form'].errors.get('file_name', []))
        self.assertIn(
            MaxOneFileUploadField.default_error_messages['min_files'],
            response.context['form'].errors.get('file', []),
        )

        # Too much files
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_0': ['file_0-token'],
                'upload-free-internal-document-form-file_1': ['file_1-token'],
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            MaxOneFileUploadField.default_error_messages['max_files'],
            response.context['form'].errors.get('file', []),
        )

        # Submit a valid form
        response = self.client.post(
            url,
            data={
                'upload-free-internal-document-form-file_name': 'My file name',
                'upload-free-internal-document-form-file_0': ['file_0-token'],
            },
            **self.default_headers,
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].data, {})

        # Save the file into the admission
        self.doctorate_admission.refresh_from_db()
        self.assertNotEqual(self.doctorate_admission.uclouvain_fac_documents, [])
        self.assertEqual(self.doctorate_admission.uclouvain_sic_documents, [])

        # Check last modification data
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.doctorate_fac_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='file_0-token',
            metadata={
                'author': self.doctorate_fac_manager_user.person.global_id,
                'explicit_name': 'My file name',
            },
        )
