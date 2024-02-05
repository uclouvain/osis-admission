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
from unittest import mock

import freezegun
from osis_async.models import AsyncTask
from django.test import override_settings

from admission.constants import PDF_MIME_TYPE
from admission.contrib.models import AdmissionTask, GeneralEducationAdmission
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests import TestCase
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory


@freezegun.freeze_time('2023-01-01')
@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class GenerateAdmissionFolderTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)

    def setUp(self):
        # Mock osis-document
        patcher = mock.patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: ['550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'] if value else []
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.change_remote_metadata')
        patched = patcher.start()
        patched.return_value = {
            'name': 'myfile',
            'mimetype': PDF_MIME_TYPE,
        }
        self.addCleanup(patcher.stop)

        # Mock the generation of the folder
        patcher = mock.patch('admission.tasks.generate_admission_folder.admission_pdf_recap')
        patched = patcher.start()
        patched.return_value = 'pdf-token'
        self.addCleanup(patcher.stop)

    def test_async_generation_with_general_education_after_sic_request(self):
        admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.MASTER_MC.name,
            uclouvain_sic_documents=[],
            uclouvain_fac_documents=[],
            status=ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC.name,
        )
        async_task = AsyncTask.objects.create(
            person=admission.candidate,
        )
        AdmissionTask.objects.create(
            type=AdmissionTask.TaskType.GENERAL_FOLDER.name,
            task=async_task,
            admission=admission,
        )

        self.assertEqual(len(admission.uclouvain_sic_documents), 0)

        with self.assertNumQueriesLessThan(20):
            from admission.tasks.generate_admission_folder import general_education_admission_analysis_folder_from_task

            general_education_admission_analysis_folder_from_task(str(async_task.uuid))

            admission.refresh_from_db()
            self.assertEqual(len(admission.uclouvain_sic_documents), 1)
            self.assertEqual(len(admission.uclouvain_fac_documents), 0)

    def test_async_generation_with_general_education_after_fac_request(self):
        admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.MASTER_MC.name,
            uclouvain_sic_documents=[],
            uclouvain_fac_documents=[],
            status=ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC.name,
        )
        async_task = AsyncTask.objects.create(
            person=admission.candidate,
        )
        AdmissionTask.objects.create(
            type=AdmissionTask.TaskType.GENERAL_FOLDER.name,
            task=async_task,
            admission=admission,
        )

        self.assertEqual(len(admission.uclouvain_fac_documents), 0)

        with self.assertNumQueriesLessThan(20):
            from admission.tasks.generate_admission_folder import general_education_admission_analysis_folder_from_task

            general_education_admission_analysis_folder_from_task(str(async_task.uuid))

            admission.refresh_from_db()
            self.assertEqual(len(admission.uclouvain_fac_documents), 1)
            self.assertEqual(len(admission.uclouvain_sic_documents), 0)
