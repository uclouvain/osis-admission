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

import freezegun
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from admission.tests import QueriesAssertionsMixin
from admission.tests.exports.test_admission_recap import BaseAdmissionRecapTestCaseMixin
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.models.enums.education_group_types import TrainingType


@freezegun.freeze_time('2023-01-01')
class DoctorateAdmissionPDFRecapApiTestCase(BaseAdmissionRecapTestCaseMixin, APITestCase, QueriesAssertionsMixin):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admission = DoctorateAdmissionFactory()
        cls.candidate = cls.admission.candidate

        other_admission = DoctorateAdmissionFactory()
        cls.other_candidate = other_admission.candidate

        cls.url = resolve_url("admission_api_v1:doctorate_pdf_recap", uuid=cls.admission.uuid)

    def test_admission_doctorate_pdf_recap_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        with self.assertNumQueriesLessThan(19):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'token': 'pdf-token'})

    def test_admission_doctorate_pdf_recap_using_api_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@freezegun.freeze_time('2023-01-01')
class GeneralEducationAdmissionPDFRecapApiTestCase(
    BaseAdmissionRecapTestCaseMixin,
    APITestCase,
    QueriesAssertionsMixin,
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.master_proposition = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.MASTER_MC.name,
        )
        cls.candidate = cls.master_proposition.candidate
        cls.bachelor_proposition = GeneralEducationAdmissionFactory(
            training__education_group_type__name=TrainingType.BACHELOR.name,
            candidate=cls.candidate,
        )

        other_admission = GeneralEducationAdmissionFactory()
        cls.other_candidate = other_admission.candidate

        cls.master_url = resolve_url("admission_api_v1:general_pdf_recap", uuid=cls.master_proposition.uuid)
        cls.bachelor_url = resolve_url("admission_api_v1:general_pdf_recap", uuid=cls.bachelor_proposition.uuid)

    def test_admission_master_general_education_pdf_recap_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        with self.assertNumQueriesLessThan(15):
            response = self.client.get(self.master_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'token': 'pdf-token'})

    def test_admission_bachelor_general_education_pdf_recap_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        with self.assertNumQueriesLessThan(16):
            response = self.client.get(self.bachelor_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'token': 'pdf-token'})

    def test_admission_general_education_pdf_recap_using_api_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate.user)
        response = self.client.get(self.master_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.master_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@freezegun.freeze_time('2023-01-01')
class ContinuingEducationAdmissionPDFRecapApiTestCase(
    BaseAdmissionRecapTestCaseMixin,
    APITestCase,
    QueriesAssertionsMixin,
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admission = ContinuingEducationAdmissionFactory()
        cls.candidate = cls.admission.candidate

        other_admission = ContinuingEducationAdmissionFactory()
        cls.other_candidate = other_admission.candidate

        cls.url = resolve_url("admission_api_v1:continuing_pdf_recap", uuid=cls.admission.uuid)

    def test_admission_continuing_education_pdf_recap_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        with self.assertNumQueriesLessThan(14):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'token': 'pdf-token'})

    def test_admission_continuing_education_pdf_recap_using_api_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
