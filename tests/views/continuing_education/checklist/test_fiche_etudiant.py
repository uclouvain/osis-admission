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
import mock
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase

from admission.models import ContinuingEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import ENTITY_CDE
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.forms.admission.continuing_education.checklist import StudentReportForm
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
    ContinuingEducationTrainingFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory


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

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user

        cls.default_headers = {'HTTP_HX-Request': 'true'}

        cls.file_metadata = {
            'name': 'myfile',
            'mimetype': PDF_MIME_TYPE,
            'explicit_name': 'My file name',
            'author': cls.sic_manager_user.person.global_id,
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

    def test_get(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:continuing-education:fiche-etudiant',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context['student_report_form'], StudentReportForm)

    def test_post(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:continuing-education:fiche-etudiant',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.post(
            url,
            data={
                'edition': 'UN',
                'payement_spread': 'on',
                'tff_label': 'foobar',
            },
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context['student_report_form'], StudentReportForm)
        self.assertTrue(response.context['student_report_form'].is_valid)

        self.continuing_admission.refresh_from_db()
        self.assertIs(self.continuing_admission.payement_spread, True)
        self.assertIs(self.continuing_admission.assessment_test_succeeded, False)
        self.assertEqual(self.continuing_admission.tff_label, 'foobar')
