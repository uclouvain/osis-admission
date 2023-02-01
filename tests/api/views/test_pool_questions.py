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
from unittest.mock import patch

import freezegun
from django.shortcuts import resolve_url
from rest_framework.test import APITestCase

from admission.calendar.admission_calendar import *
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory


class PoolQuestionApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearFactory.produce(number_future=6)
        for pool in [
            DoctorateAdmissionCalendar,
            ContinuingEducationAdmissionCalendar,
            AdmissionPoolExternalEnrollmentChangeCalendar,
            AdmissionPoolExternalReorientationCalendar,
            AdmissionPoolVipCalendar,
            AdmissionPoolHueUclPathwayChangeCalendar,
            AdmissionPoolInstituteChangeCalendar,
            AdmissionPoolUe5BelgianCalendar,
            AdmissionPoolUe5NonBelgianCalendar,
            AdmissionPoolHue5BelgiumResidencyCalendar,
            AdmissionPoolHue5ForeignResidencyCalendar,
            AdmissionPoolNonResidentQuotaCalendar,
        ]:
            pool.ensure_consistency_until_n_plus_6()

    @freezegun.freeze_time('2022-08-01')
    def test_pool_question_api_get_with_not_bachelor(self):
        admission = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.AGGREGATION.name,
        )
        self.client.force_authenticate(admission.candidate.user)
        url = resolve_url('admission_api_v1:pool-questions', uuid=admission.uuid)
        response = self.client.get(url)
        self.assertDictEqual({}, response.json())

    @freezegun.freeze_time('2022-08-01')
    def test_pool_question_api_get_with_no_question(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.BACHELOR.name)
        self.client.force_authenticate(admission.candidate.user)
        url = resolve_url('admission_api_v1:pool-questions', uuid=admission.uuid)
        response = self.client.get(url)
        self.assertDictEqual({}, response.json())

    @freezegun.freeze_time('2022-08-01')
    def test_pool_question_api_get_with_residency(self):
        admission = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.BACHELOR.name,
            training__acronym=SIGLES_WITH_QUOTA[0],
        )
        self.client.force_authenticate(admission.candidate.user)
        url = resolve_url('admission_api_v1:pool-questions', uuid=admission.uuid)
        response = self.client.get(url)
        expected = {
            'modification_pool_end_date': None,
            'reorientation_pool_end_date': None,
            'is_non_resident': None,
        }
        self.assertDictEqual(expected, response.json())

    @freezegun.freeze_time('2023-01-15')
    def test_pool_question_api_get_with_reorientation(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.BACHELOR.name)
        self.client.force_authenticate(admission.candidate.user)
        url = resolve_url('admission_api_v1:pool-questions', uuid=admission.uuid)
        response = self.client.get(url)
        expected = {
            'modification_pool_end_date': None,
            'reorientation_pool_end_date': '2023-02-15T23:59:00',
            'is_belgian_bachelor': None,
            'is_external_reorientation': None,
            'regular_registration_proof': [],
        }
        self.assertDictEqual(expected, response.json())

    @freezegun.freeze_time('2023-01-15')
    def test_pool_question_api_get_with_residency_and_reorientation(self):
        admission = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.BACHELOR.name,
            training__acronym=SIGLES_WITH_QUOTA[0],
        )
        self.client.force_authenticate(admission.candidate.user)
        url = resolve_url('admission_api_v1:pool-questions', uuid=admission.uuid)
        response = self.client.get(url)
        expected = {
            'modification_pool_end_date': None,
            'reorientation_pool_end_date': '2023-02-15T23:59:00',
            'is_non_resident': None,
            'is_belgian_bachelor': None,
            'is_external_reorientation': None,
            'regular_registration_proof': [],
        }
        self.assertDictEqual(expected, response.json())

    @freezegun.freeze_time('2022-10-15')
    def test_pool_question_api_get_with_modification(self):
        admission = GeneralEducationAdmissionFactory(training__education_group_type__name=TrainingType.BACHELOR.name)
        self.client.force_authenticate(admission.candidate.user)
        url = resolve_url('admission_api_v1:pool-questions', uuid=admission.uuid)
        response = self.client.get(url)
        expected = {
            'modification_pool_end_date': '2022-10-31T23:59:00',
            'reorientation_pool_end_date': None,
            'is_belgian_bachelor': None,
            'is_external_modification': None,
            'registration_change_form': [],
        }
        self.assertDictEqual(expected, response.json())

    @freezegun.freeze_time('2022-08-01')
    @patch('osis_document.api.utils.get_remote_metadata')
    @patch('osis_document.api.utils.confirm_remote_upload')
    def test_pool_question_api_update_with_residency(self, confirm, get_remote_metadata):
        confirm.return_value = '4bdffb42-552d-415d-9e4c-725f10dce228'
        get_remote_metadata.return_value = {"name": "test.pdf"}
        # Pool questions are inconsistent and should be removed
        admission = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.BACHELOR.name,
            training__acronym=SIGLES_WITH_QUOTA[0],
            is_belgian_bachelor=True,
            is_external_reorientation=True,
            registration_change_form=['uuid'],
        )
        self.client.force_authenticate(admission.candidate.user)
        url = resolve_url('admission_api_v1:pool-questions', uuid=admission.uuid)
        response = self.client.get(url)
        expected = {
            'modification_pool_end_date': None,
            'reorientation_pool_end_date': None,
            'is_non_resident': None,
        }
        self.assertDictEqual(expected, response.json())

        response = self.client.put(url, {'is_non_resident': False})
        expected = {
            'is_non_resident': False,
            # The rest should be set to default
            'modification_pool_end_date': None,
            'reorientation_pool_end_date': None,
            'is_belgian_bachelor': None,
            'is_external_modification': None,
            'is_external_reorientation': None,
            'registration_change_form': [],
            'regular_registration_proof': [],
        }
        self.assertDictEqual(expected, response.json())
        admission.refresh_from_db()
        self.assertIsNone(admission.is_external_reorientation)
        self.assertIsNone(admission.is_belgian_bachelor)
        self.assertEqual(admission.registration_change_form, [])
