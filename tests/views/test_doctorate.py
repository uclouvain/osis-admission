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

from django.test import tag
from django.urls import reverse

from admission.contrib.models import DoctorateAdmission, AdmissionType
from admission.tests import TestCase
from admission.tests.factories import DoctorateAdmissionFactory
from base.models.enums.entity_type import SECTOR
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class DoctorateAdmissionCreateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate = PersonFactory()
        cls.url = reverse("admission:doctorate-create:project")
        cls.data = {
            "comment": "this is a test",
            "type": AdmissionType.ADMISSION.name,
        }
        EntityVersionFactory(acronym='CDE')

    def test_create_doctorate_admission_user_is_candidate(self):
        self.client.force_login(self.candidate.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertEqual(response.status_code, 200)
        # Check that the created object got the person as author
        admission_author = DoctorateAdmission.objects.get().candidate
        self.assertEqual(admission_author, self.candidate)

    def test_create_doctorate_admission_redirect_to_detail_view(self):
        self.client.force_login(self.candidate.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertEqual(response.status_code, 200)
        # make sure that the DoctorateAdmission creation redirect to the detail view
        self.assertTemplateUsed(
            response,
            "admission/doctorate/detail_person.html",
        )

    def test_view_context_data_contains_CDE_id(self):
        self.client.force_login(self.candidate.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["CDE_id"])


class DoctorateAdmissionListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        DoctorateAdmissionFactory(
            candidate=cls.person,
            type=AdmissionType.ADMISSION.name,
            comment="First admission",
        )
        DoctorateAdmissionFactory(
            candidate=cls.person,
            type=AdmissionType.ADMISSION.name,
            comment="Second admission",
        )
        DoctorateAdmissionFactory(
            candidate=cls.person,
            type=AdmissionType.PRE_ADMISSION.name,
            comment="A pre-admission",
        )
        cls.url = reverse("admission:doctorate-list")

    def test_view_context_data_contains_items_per_page(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["items_per_page"])

    def test_filtering_by_admission_type(self):
        self.client.force_login(self.person.user)
        response = self.client.get(
            self.url, data={"type": AdmissionType.ADMISSION.name}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data["object_list"]), 2)

    def test_filtering_by_pre_admission_type(self):
        self.client.force_login(self.person.user)
        response = self.client.get(
            self.url, data={"type": AdmissionType.PRE_ADMISSION.name}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data["object_list"]), 1)

    def test_filtering_by_candidate(self):
        self.client.force_login(self.person.user)
        response = self.client.get(
            self.url, data={"candidate": self.person.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data["object_list"]), 3)

    @tag('perf')
    def test_get_num_queries_serializer(self):
        self.client.force_login(self.person.user)
        with self.assertNumQueriesLessThan(13):
            self.client.get(self.url, HTTP_ACCEPT='application/json')


class DoctorateAdmissionUpdateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate = PersonFactory()
        cls.new_candidate = PersonFactory()
        cls.admission = DoctorateAdmissionFactory(
            candidate=cls.candidate,
            comment="A comment",
            type=AdmissionType.ADMISSION,
        )
        sector = EntityVersionFactory(entity_type=SECTOR).entity_id
        cls.update_data = {
            "type": AdmissionType.PRE_ADMISSION.name,
            "comment": "New comment",
            "sector": sector,
            "doctorate": EntityVersionFactory(parent_id=sector).entity_id,
        }
        cls.url = reverse("admission:doctorate-update:project", args=[cls.admission.pk])

    def test_doctorate_admission_is_updated(self):
        self.client.force_login(self.candidate.user)
        response = self.client.post(self.url, data=self.update_data)
        self.assertEqual(response.status_code, 302)
        admission = DoctorateAdmission.objects.get(pk=self.admission.pk)
        admission.refresh_from_db()
        self.assertEqual(admission.comment, self.update_data["comment"])
        self.assertEqual(admission.type, self.update_data["type"])
