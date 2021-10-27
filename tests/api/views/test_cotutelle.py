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
from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from admission.contrib.models import DoctorateAdmission
from admission.tests.factories import DoctorateAdmissionFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class CotutelleApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admission = DoctorateAdmissionFactory()
        cls.candidate = cls.admission.candidate
        cls.url = resolve_url("cotutelle", uuid=cls.admission.uuid)

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

    def test_cotutelle_update_using_api(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data={
            'motivation': "A good motive",
            'institution': "Famous institution",
            'demande_ouverture': [],
            'convention': [],
            'autres_documents': [],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        admission = DoctorateAdmission.objects.get()
        self.assertEqual(admission.cotutelle_institution, "Famous institution")

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.json()['institution'], "Famous institution")
