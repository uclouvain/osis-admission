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

from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from admission.contrib.models import DoctorateAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.roles import CandidateFactory
from admission.tests.factories.supervision import CaMemberFactory, PromoterFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.person import PersonFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class CotutelleApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        doctoral_commission = EntityFactory()
        cls.admission = DoctorateAdmissionFactory(training__management_entity=doctoral_commission, cotutelle=None)
        cls.updated_data = {
            'motivation': "A good motive",
            'institution_fwb': False,
            'institution': "5c2f68f3-f834-4638-8047-a507d7f26ba6",
            'demande_ouverture': [],
            'convention': [],
            'autres_documents': [],
        }
        AdmissionAcademicCalendarFactory.produce_all_required()
        # Targeted url
        cls.url = resolve_url("cotutelle", uuid=cls.admission.uuid)
        # Create an admission supervision group
        promoter = PromoterFactory()
        committee_member = CaMemberFactory(process=promoter.process)
        cls.admission.supervision_group = promoter.process
        cls.admission.save()
        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate_user = CandidateFactory().person.user
        cls.no_role_user = PersonFactory().user
        cls.promoter_user = promoter.person.user
        cls.other_promoter_user = PromoterFactory().person.user
        cls.committee_member_user = committee_member.person.user
        cls.other_committee_member_user = CaMemberFactory().person.user

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['delete', 'post', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cotutelle_get_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_cotutelle_update_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.put(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_cotutelle_get_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_cotutelle_update_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        admission = DoctorateAdmission.objects.get()
        self.assertIsNone(admission.cotutelle)

        response = self.client.put(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        admission = DoctorateAdmission.objects.get()
        self.assertTrue(admission.cotutelle)
        self.assertEqual(str(admission.cotutelle_institution), "5c2f68f3-f834-4638-8047-a507d7f26ba6")

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.json()['institution'], "5c2f68f3-f834-4638-8047-a507d7f26ba6")

    def test_cotutelle_get_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_cotutelle_update_other_candidate(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.put(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_cotutelle_get_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_cotutelle_update_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.put(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_cotutelle_get_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_cotutelle_update_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.put(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_cotutelle_get_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_cotutelle_update_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.put(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)
