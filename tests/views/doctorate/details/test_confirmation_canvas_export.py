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
import datetime
import uuid
from typing import Optional
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_302_FOUND, HTTP_200_OK

from admission.contrib.models import ConfirmationPaper
from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixTypeAdmission
from admission.ddd.projet_doctoral.preparation.domain.model._financement import (
    ChoixTypeFinancement,
    ChoixTypeContratTravail,
)
from admission.ddd.projet_doctoral.preparation.domain.model.doctorat import ENTITY_CDE
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.confirmation_paper import ConfirmationPaperFactory
from admission.tests.factories.roles import CddManagerFactory
from admission.tests.factories.supervision import PromoterFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DoctorateAdmissionConfirmationCanvasExportViewTestCase(TestCase):
    admission_with_confirmation_paper: Optional[DoctorateAdmissionFactory] = None
    admission_without_confirmation_paper: Optional[DoctorateAdmissionFactory] = None
    confirmation_paper: Optional[ConfirmationPaperFactory] = None

    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        # Create admissions
        cls.admission_without_confirmation_paper = DoctorateAdmissionFactory(
            doctorate__management_entity=first_doctoral_commission,
            doctorate__academic_year=academic_years[0],
            cotutelle=False,
            supervision_group=PromoterFactory().process,
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_ASSISTANT.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            pre_admission_submission_date=datetime.datetime.now(),
            admitted=True,
        )
        cls.admission_with_confirmation_paper = DoctorateAdmissionFactory(
            doctorate__management_entity=first_doctoral_commission,
            doctorate__academic_year=academic_years[0],
            cotutelle=False,
            supervision_group=PromoterFactory().process,
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_ASSISTANT.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            pre_admission_submission_date=datetime.datetime.now(),
            admitted=True,
        )
        cls.confirmation_paper = ConfirmationPaperFactory(
            admission=cls.admission_with_confirmation_paper,
            confirmation_date=datetime.date(2022, 4, 1),
            confirmation_deadline=datetime.date(2022, 4, 5),
        )

        cls.candidate = cls.admission_without_confirmation_paper.candidate

        # User with one cdd
        cls.cdd_person = CddManagerFactory(entity=first_doctoral_commission).person

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

    def test_confirmation_canvas_export_candidate_user_is_forbidden(self):
        self.client.force_login(user=self.candidate.user)

        url = reverse(self.path_name, args=[self.admission_with_confirmation_paper.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_confirmation_canvas_export_cdd_user_with_unknown_doctorate_returns_not_found(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path_name, args=[uuid.uuid4()])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_confirmation_canvas_export_cdd_user_without_confirmation_paper_returns_not_found(self):
        self.client.force_login(user=self.cdd_person.user)

        url = reverse(self.path_name, args=[self.admission_without_confirmation_paper.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_confirmation_canvas_export_cdd_user_with_confirmation_paper_redirects_to_file_url(self):
        self.client.force_login(user=self.cdd_person.user)

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
