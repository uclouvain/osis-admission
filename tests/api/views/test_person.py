# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from admission.tests.factories.groups import CandidateGroupFactory, PromoterGroupFactory,\
    CddManagerGroupFactory, CommitteeMemberGroupFactory
from base.tests.factories.person import PersonFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class PersonTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('person')
        cls.updated_data = {
            "first_name": "Jo"
        }
        cls.candidate_user = PersonFactory(first_name="John").user
        cls.candidate_user.groups.add(CandidateGroupFactory())
        cls.no_role_user = PersonFactory(first_name="Joe").user
        cls.cdd_manager_user = PersonFactory(first_name="Jack").user
        cls.cdd_manager_user.groups.add(CddManagerGroupFactory())
        cls.promoter_user = PersonFactory(first_name="Jane").user
        cls.promoter_user.groups.add(PromoterGroupFactory())
        cls.committee_member_user = PersonFactory(first_name="James").user
        cls.committee_member_user.groups.add(CommitteeMemberGroupFactory())

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate_user)
        methods_not_allowed = ['delete', 'post', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_person_get_no_role(self):
        self.client.force_authenticate(self.no_role_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.json())

    def test_person_update_no_role(self):
        self.client.force_authenticate(self.no_role_user)
        response = self.client.put(self.url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.json())

    def test_person_get_candidate(self):
        self.client.force_authenticate(self.candidate_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(response.json()['first_name'], "John")

    def test_person_update_candidate(self):
        self.client.force_authenticate(self.candidate_user)
        response = self.client.put(self.url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(response.json()['first_name'], "Jo")

    def test_person_get_cdd_manager(self):
        self.client.force_authenticate(self.cdd_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(response.json()['first_name'], "Jack")

    def test_person_update_cdd_manager(self):
        self.client.force_authenticate(self.cdd_manager_user)
        response = self.client.put(self.url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(response.json()['first_name'], "Jo")

    def test_person_get_promoter(self):
        self.client.force_authenticate(self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(response.json()['first_name'], "Jane")

    def test_person_update_promoter(self):
        self.client.force_authenticate(self.promoter_user)
        response = self.client.put(self.url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.json())

    def test_person_get_committee_member(self):
        self.client.force_authenticate(self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(response.json()['first_name'], "James")

    def test_person_update_committee_member(self):
        self.client.force_authenticate(self.committee_member_user)
        response = self.client.put(self.url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.json())
