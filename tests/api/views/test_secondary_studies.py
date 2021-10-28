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

from admission.tests.factories.secondary_studies import BelgianHighSchoolDiplomaFactory, ForeignHighSchoolDiplomaFactory
from osis_profile.models import BelgianHighSchoolDiploma, ForeignHighSchoolDiploma


class BelgianHighSchoolDiplomaTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.belgian_diploma = BelgianHighSchoolDiplomaFactory(institute="Test Institute")
        cls.user = cls.belgian_diploma.person.user
        cls.url = reverse("admission_api_v1:secondary-studies")

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.user)
        methods_not_allowed = ["delete", "post", "patch"]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_diploma_get(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.json()["belgian_diploma"]["institute"], "Test Institute")

    def test_diploma_update(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(self.url, {
            "belgian_diploma": {
                "institute": "Institute Of Test",
                "academic_graduation_year": 2021,
            },
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        diploma = BelgianHighSchoolDiploma.objects.get(person__user_id=self.user.pk)
        self.assertEqual(diploma.institute, "Institute Of Test")


class ForeignHighSchoolDiplomaTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.foreign_diploma = ForeignHighSchoolDiplomaFactory(other_linguistic_regime="Franglais")
        cls.user = cls.foreign_diploma.person.user
        cls.url = reverse("admission_api_v1:secondary-studies")

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.user)
        methods_not_allowed = ["delete", "post", "patch"]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_diploma_get(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.json()["foreign_diploma"]["other_linguistic_regime"], "Franglais")

    def test_diploma_update(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(self.url, {
            "foreign_diploma": {
                "other_linguistic_regime": "Français",
                "academic_graduation_year": 2021,
                "linguistic_regime": self.foreign_diploma.linguistic_regime.code,
                "country": self.foreign_diploma.country.iso_code,
            },
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        diploma = ForeignHighSchoolDiploma.objects.get(person__user_id=self.user.pk)
        self.assertEqual(diploma.other_linguistic_regime, "Français")
