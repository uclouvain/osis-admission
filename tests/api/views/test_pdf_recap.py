# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from unittest import mock

import freezegun
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from admission.constants import PDF_MIME_TYPE
from admission.tests import QueriesAssertionsMixin
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory
from base.models.enums.education_group_types import TrainingType


@freezegun.freeze_time('2023-01-01')
class PDFRecapApiTestCase(APITestCase, QueriesAssertionsMixin):
    @classmethod
    def setUpTestData(cls):
        doctorate_admission = DoctorateAdmissionFactory()
        master_proposition = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.MASTER_MC.name,
            candidate=doctorate_admission.candidate,
        )
        bachelor_proposition = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.BACHELOR.name,
            candidate=doctorate_admission.candidate,
        )
        continuation_admission = ContinuingEducationAdmissionFactory(
            candidate=doctorate_admission.candidate,
        )
        cls.candidate = doctorate_admission.candidate.user
        cls.other_candidate = CandidateFactory().person.user

        cls.doctorate_url = resolve_url("admission_api_v1:doctorate_pdf_recap", uuid=doctorate_admission.uuid)
        cls.master_url = resolve_url("admission_api_v1:general_pdf_recap", uuid=master_proposition.uuid)
        cls.bachelor_url = resolve_url("admission_api_v1:general_pdf_recap", uuid=bachelor_proposition.uuid)
        cls.continuing_url = resolve_url("admission_api_v1:continuing_pdf_recap", uuid=continuation_admission.uuid)

    def setUp(self):
        patcher = mock.patch('admission.exports.admission_recap.admission_recap.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids: {uuid: f'token-{index}' for index, uuid in enumerate(uuids)}
        self.addCleanup(patcher.stop)

        patcher = mock.patch('admission.exports.admission_recap.admission_recap.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {
            token: {
                'name': 'myfile',
                'mimetype': PDF_MIME_TYPE,
            }
            for token in tokens
        }
        self.addCleanup(patcher.stop)

        save_raw_content_remotely_patcher = mock.patch('osis_document.utils.save_raw_content_remotely')
        patched = save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'
        self.addCleanup(save_raw_content_remotely_patcher.stop)

        # Mock weasyprint
        patcher = mock.patch('admission.exports.utils.get_pdf_from_template', return_value=b'some content')
        patcher.start()
        self.addCleanup(patcher.stop)

        # Mock pikepdf
        patcher = mock.patch('admission.exports.admission_recap.admission_recap.Pdf')
        patched = patcher.start()
        patched.new.return_value = mock.MagicMock(pdf_version=1)
        self.outline_root = (
            patched.new.return_value.open_outline.return_value.__enter__.return_value.root
        ) = mock.MagicMock()
        patched.open.return_value.__enter__.return_value = mock.Mock(pdf_version=1, pages=[None])
        self.addCleanup(patcher.stop)

        patcher = mock.patch('admission.exports.admission_recap.attachments.get_raw_content_remotely')
        self.get_raw_content_mock = patcher.start()
        self.get_raw_content_mock.return_value = b'some content'
        self.addCleanup(patcher.stop)

        patcher = mock.patch('admission.exports.admission_recap.admission_recap.save_raw_content_remotely')
        self.save_raw_content_mock = patcher.start()
        self.save_raw_content_mock.return_value = 'pdf-token'
        self.addCleanup(patcher.stop)

    def test_doctorate_admission_doctorate_pdf_recap_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate)
        with self.assertNumQueriesLessThan(19):
            response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'token': 'pdf-token'})

    def test_doctorate_admission_doctorate_pdf_recap_using_api_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate)
        response = self.client.get(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_doctorate_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admission_master_general_education_pdf_recap_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate)
        with self.assertNumQueriesLessThan(15):
            response = self.client.get(self.master_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'token': 'pdf-token'})

    def test_admission_bachelor_general_education_pdf_recap_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate)
        with self.assertNumQueriesLessThan(16):
            response = self.client.get(self.bachelor_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'token': 'pdf-token'})

    def test_admission_general_education_pdf_recap_using_api_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate)
        response = self.client.get(self.master_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.doctorate_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(self.master_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(self.bachelor_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(self.continuing_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admission_continuing_education_pdf_recap_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate)
        with self.assertNumQueriesLessThan(14):
            response = self.client.get(self.continuing_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'token': 'pdf-token'})

    def test_admission_continuing_education_pdf_recap_using_api_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate)
        response = self.client.get(self.continuing_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
