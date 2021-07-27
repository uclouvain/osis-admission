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

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from admission.contrib.models import AdmissionType, DoctorateAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from base.tests.factories.person import PersonFactory


class DoctorateAdmissionApiTestCase(TestCase):
    client_class = APIClient

    @classmethod
    def setUpTestData(cls):
        cls.author = PersonFactory()
        cls.candidate = PersonFactory()
        cls.create_data = {
            "type": AdmissionType.PRE_ADMISSION.name,
            "candidate": cls.candidate.pk,
            "comment": "test admission doctorate serializer",
        }
        cls.create_url = reverse("admission_api_v1:doctorate-list")
        cls.admission = DoctorateAdmissionFactory(
            type=AdmissionType.PRE_ADMISSION.name,
            candidate=cls.author,
            author=cls.author,
            comment="test admission doctorate serializer",
        )
        cls.update_data = {
            "type": AdmissionType.ADMISSION.name,
            "candidate": cls.candidate.pk,
            "comment": "updated comment",
        }
        cls.update_url = reverse(
            "admission_api_v1:doctorate-detail",
            args=[cls.admission.uuid],
        )

    def test_admission_doctorate_creation_using_api(self):
        self.client.force_login(self.author.user)
        response = self.client.post(self.create_url, data=self.create_data)
        self.assertEqual(response.status_code, 201)
        admissions = DoctorateAdmission.objects.all()
        self.assertEqual(admissions.count(), 2)
        admission = admissions.get(uuid=response.data["uuid"])
        self.assertEqual(admission.author, self.author)
        self.assertEqual(admission.type, self.create_data["type"])
        self.assertEqual(admission.candidate.pk, self.create_data["candidate"])
        self.assertEqual(admission.comment, self.create_data["comment"])

    def test_admission_doctorate_update_using_api(self):
        self.client.force_login(self.author.user)
        response = self.client.patch(
            self.update_url,
            data=self.update_data,
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        admissions = DoctorateAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)
        # The author must not change
        self.assertEqual(admissions.get().author, self.author)
        # But all the following should
        self.assertEqual(admissions.get().type, self.update_data["type"])
        self.assertEqual(admissions.get().candidate.pk, self.update_data["candidate"])
        self.assertEqual(admissions.get().comment, self.update_data["comment"])
