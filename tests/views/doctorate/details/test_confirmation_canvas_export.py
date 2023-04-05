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

import datetime
import uuid
from typing import Optional
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.status import HTTP_302_FOUND, HTTP_404_NOT_FOUND

from admission.contrib.models import ConfirmationPaper
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.confirmation_paper import ConfirmationPaperFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.program_manager import ProgramManagerFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DoctorateConfirmationCanvasExportViewTestCase(TestCase):
    admission_with_confirmation_paper: Optional[DoctorateAdmissionFactory] = None
    admission_without_confirmation_paper: Optional[DoctorateAdmissionFactory] = None
    confirmation_paper: Optional[ConfirmationPaperFactory] = None

    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # Create admissions
        cls.admission_without_confirmation_paper = DoctorateAdmissionFactory(
            training__academic_year=academic_years[0],
            admitted=True,
        )
        cls.admission_with_confirmation_paper = DoctorateAdmissionFactory(
            training=cls.admission_without_confirmation_paper.training,
            admitted=True,
        )
        cls.confirmation_paper = ConfirmationPaperFactory(
            admission=cls.admission_with_confirmation_paper,
            confirmation_date=datetime.date(2022, 4, 1),
            confirmation_deadline=datetime.date(2022, 4, 5),
        )

        cls.manager = ProgramManagerFactory(
            education_group=cls.admission_without_confirmation_paper.training.education_group
        ).person.user

        # Targeted path
        cls.path_name = 'admission:doctorate:confirmation-canvas'

        # Mock osis-document
        cls.confirm_remote_upload_patcher = patch('osis_document.api.utils.confirm_remote_upload')
        patched = cls.confirm_remote_upload_patcher.start()
        patched.return_value = '4bdffb42-552d-415d-9e4c-725f10dce228'

        cls.get_remote_metadata_patcher = patch('osis_document.api.utils.get_remote_metadata')
        patched = cls.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf"}

        cls.get_remote_token_patcher = patch('osis_document.api.utils.get_remote_token')
        patched = cls.get_remote_token_patcher.start()
        patched.return_value = 'b-token'

        cls.save_raw_content_remotely_patcher = patch('osis_document.utils.save_raw_content_remotely')
        patched = cls.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'

    @classmethod
    def tearDownClass(cls):
        cls.confirm_remote_upload_patcher.stop()
        cls.get_remote_metadata_patcher.stop()
        cls.get_remote_token_patcher.stop()
        cls.save_raw_content_remotely_patcher.stop()
        super().tearDownClass()

    def setUp(self):
        self.client.force_login(user=self.manager)

        # Mock weasyprint
        patcher = patch('admission.exports.utils.get_pdf_from_template', return_value=b'some content')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_confirmation_canvas_export_cdd_user_without_confirmation_paper_returns_not_found(self):
        url = reverse(self.path_name, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_confirmation_canvas_export_cdd_user_with_confirmation_paper_redirects_to_file_url(self):
        url = reverse(self.path_name, args=[self.admission_with_confirmation_paper.uuid])

        response = self.client.get(url)

        # Check response
        self.assertEqual(response.status_code, HTTP_302_FOUND)
        self.assertEqual(response.url, 'http://dummyurl/file/b-token')

        # Check saved data
        confirmation_paper = ConfirmationPaper.objects.get(uuid=self.confirmation_paper.uuid)
        self.assertEqual(
            confirmation_paper.supervisor_panel_report_canvas,
            [uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')],
        )
