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
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from admission.tests.factories.groups import CandidateGroupFactory, CddManagerGroupFactory, CommitteeMemberGroupFactory, PromoterGroupFactory

from base.models.enums.person_address_type import PersonAddressType
from base.models.person_address import PersonAddress
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_address import PersonAddressFactory


class PersonTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Targeted url
        cls.url = reverse('admission_api_v1:coordonnees')
        # Data
        cls.updated_data = {
            "residential": {'street': "Rue de la sobriété"},
            "contact": {},
            "phone_mobile": "",
        }
        cls.address = PersonAddressFactory(
            label=PersonAddressType.CONTACT.value,
            street="Rue de la soif",
        )
        # Users
        cls.candidate_user = cls.address.person.user
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

    def test_coordonnees_get_no_role(self):
        self.client.force_authenticate(self.no_role_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.json())

    def test_coordonnees_update_no_role(self):
        self.client.force_authenticate(self.no_role_user)
        response = self.client.put(self.url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.json())

    def test_coordonnees_get_candidate(self):
        self.client.force_authenticate(self.candidate_user)
        response = self.client.get(self.url)
        self.assertEqual(response.json()['contact']['street'], "Rue de la soif")

    def test_coordonnees_update_candidate(self):
        self.client.force_authenticate(self.candidate_user)
        response = self.client.put(self.url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        address = PersonAddress.objects.get(person__user_id=self.candidate_user.pk, label=PersonAddressType.RESIDENTIAL.value)
        self.assertEqual(address.street, "Rue de la sobriété")

    def test_coordonnees_get_cdd_manager(self):
        self.client.force_authenticate(self.cdd_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

    def test_coordonnees_update_cdd_manager(self):
        self.client.force_authenticate(self.cdd_manager_user)
        response = self.client.put(self.url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

    def test_coordonnees_get_cdd_manager(self):
        self.client.force_authenticate(self.cdd_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

    def test_coordonnees_update_cdd_manager(self):
        self.client.force_authenticate(self.cdd_manager_user)
        response = self.client.put(self.url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

    def test_coordonnees_get_promoter(self):
        self.client.force_authenticate(self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

    def test_coordonnees_update_promoter(self):
        self.client.force_authenticate(self.promoter_user)
        response = self.client.put(self.url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.json())

    def test_coordonnees_get_committee_member(self):
        self.client.force_authenticate(self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

    def test_coordonnees_update_committee_member(self):
        self.client.force_authenticate(self.committee_member_user)
        response = self.client.put(self.url, self.updated_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.json())
