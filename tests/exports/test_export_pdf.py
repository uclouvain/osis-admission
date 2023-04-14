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

from unittest.mock import ANY, patch

from django.core.management import call_command
from django.test import TestCase

from admission.contrib.models import AdmissionTask
from admission.tests.factories import DoctorateAdmissionFactory
from osis_async.models import AsyncTask
from osis_async.models.enums import TaskState
from osis_document.contrib.post_processing.post_processing_enums import PostProcessingEnums


class ExportPdfTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admission = DoctorateAdmissionFactory()

    def setUp(self):
        # Mock weasyprint
        patcher = patch('admission.exports.utils.get_pdf_from_template', return_value=b'some content')
        patcher.start()
        self.addCleanup(patcher.stop)

    @patch('osis_document.api.utils.launch_post_processing')
    @patch('osis_document.api.utils.get_remote_metadata')
    @patch('osis_document.utils.save_raw_content_remotely')
    @patch('osis_document.api.utils.confirm_remote_upload')
    def test_pdf_archive(self, confirm, save, get_metadata, post_processing):
        get_metadata.return_value = {"name": "test.pdf"}
        save.return_value = 'a-token'
        confirm.return_value = '4bdffb42-552d-415d-9e4c-725f10dce228'
        post_processing.return_value = {
            PostProcessingEnums.MERGE_PDF.name: {'output': ['4bdffb42-552d-415d-9e4c-725f10dce228']}
        }
        async_task = AsyncTask.objects.create(name="Export pdf")
        AdmissionTask.objects.create(
            admission=self.admission,
            type=AdmissionTask.TaskType.ARCHIVE.name,
            task=async_task,
        )
        call_command("process_admission_tasks")
        save.assert_called()
        confirm.assert_called_with('a-token')
        async_task.refresh_from_db()
        self.assertEqual(async_task.state, TaskState.DONE.name)

    @patch('osis_document.utils.save_raw_content_remotely')
    @patch('osis_document.api.utils.confirm_remote_upload')
    def test_pdf_archive_with_error(self, confirm, save):
        save.side_effect = Exception("API not working")
        async_task = AsyncTask.objects.create(name="Export pdf")
        AdmissionTask.objects.create(
            admission=self.admission,
            type=AdmissionTask.TaskType.ARCHIVE.name,
            task=async_task,
        )
        with self.assertRaises(Exception):
            call_command("process_admission_tasks")
        save.assert_called()
        confirm.assert_not_called()
        async_task.refresh_from_db()
        self.assertEqual(async_task.state, TaskState.PENDING.name)
