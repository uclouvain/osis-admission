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
from django.utils.translation import gettext

from admission.tests.views.common.detail_tabs.test_document import BaseDocumentViewTestCase


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class AnalysisFolderGenerationTestCase(BaseDocumentViewTestCase):
    @freezegun.freeze_time('2022-01-01')
    def test_general_sic_manager_generates_new_analysis_folder(self):
        self._mock_folder_generation()

        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:document:analysis-folder-generation',
            uuid=self.general_admission.uuid,
        )

        # Submit a valid form
        response = self.client.post(url, **self.default_headers)

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
            token='pdf-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': gettext('Analysis folder'),
            },
        )

    @freezegun.freeze_time('2022-01-01')
    def test_continuing_sic_manager_generates_new_analysis_folder(self):
        self._mock_folder_generation()

        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:continuing-education:document:analysis-folder-generation',
            uuid=self.continuing_admission.uuid,
        )

        # Submit a valid form
        response = self.client.post(url, **self.default_headers)

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
            token='pdf-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': gettext('Analysis folder'),
            },
        )

    @freezegun.freeze_time('2022-01-01')
    def test_continuing_fac_manager_generates_new_analysis_folder(self):
        self._mock_folder_generation()

        self.client.force_login(user=self.continuing_fac_manager_user)

        url = resolve_url(
            'admission:continuing-education:document:analysis-folder-generation',
            uuid=self.continuing_admission.uuid,
        )

        # Submit a valid form
        response = self.client.post(url, **self.default_headers)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].data, {})

        # Save the file into the admission
        self.continuing_admission.refresh_from_db()
        self.assertEqual(self.continuing_admission.uclouvain_sic_documents, [])
        self.assertNotEqual(self.continuing_admission.uclouvain_fac_documents, [])

        # Check last modification data
        self.assertEqual(self.continuing_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.continuing_admission.last_update_author, self.continuing_fac_manager_user.person)

        # Save the author and the explicit name into the file
        self.change_remote_metadata_patcher.assert_called_once_with(
            token='pdf-token',
            metadata={
                'author': self.continuing_fac_manager_user.person.global_id,
                'explicit_name': gettext('Analysis folder'),
            },
        )

    @freezegun.freeze_time('2022-01-01')
    def test_doctorate_sic_manager_generates_new_analysis_folder(self):
        self._mock_folder_generation()

        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:doctorate:document:analysis-folder-generation',
            uuid=self.doctorate_admission.uuid,
        )

        # Submit a valid form
        response = self.client.post(url, **self.default_headers)

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
            token='pdf-token',
            metadata={
                'author': self.sic_manager_user.person.global_id,
                'explicit_name': gettext('Analysis folder'),
            },
        )
