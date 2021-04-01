from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from admission.contrib.models import AdmissionType, AdmissionDoctorate
from admission.tests.factories import AdmissionDoctorateFactory
from base.tests.factories.person import PersonFactory


class AdmissionDoctorateApiTestCase(TestCase):
    client_class = APIClient

    @classmethod
    def setUpTestData(cls):
        cls.author = PersonFactory()
        cls.candidate = PersonFactory()
        cls.create_data = {
            "type_select": AdmissionType.PRE_ADMISSION.name,
            "candidate_write": cls.candidate.pk,
            "comment": "test admission doctorate serializer",
        }
        cls.create_url = reverse("admissions:doctorate-api-list")
        cls.admission = AdmissionDoctorateFactory(
            type=AdmissionType.PRE_ADMISSION.name,
            candidate=cls.author,
            author=cls.author,
            comment="test admission doctorate serializer",
        )
        cls.update_data = {
            "type_select": AdmissionType.ADMISSION.name,
            "candidate_write": cls.candidate.pk,
            "comment": "updated comment",
        }
        cls.update_url = reverse(
            "admissions:doctorate-api-detail",
            args=[cls.admission.uuid],
        )

    def test_admission_doctorate_creation_using_api(self):
        self.client.force_login(self.author.user)
        response = self.client.post(self.create_url, data=self.create_data)
        self.assertEqual(response.status_code, 201)
        admissions = AdmissionDoctorate.objects.all()
        self.assertEqual(admissions.count(), 2)
        admission = admissions.get(uuid=response.data["uuid"])
        self.assertEqual(admission.author, self.author)
        self.assertEqual(admission.candidate, self.candidate)
        self.assertEqual(admission.comment, self.create_data["comment"])

    def test_admission_doctorate_update_using_api(self):
        self.client.force_login(self.author.user)
        response = self.client.patch(
            self.update_url,
            data=self.update_data,
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        admissions = AdmissionDoctorate.objects.all()
        self.assertEqual(admissions.count(), 1)
        # The author must not change
        self.assertEqual(admissions.get().author, self.author)
        # But all the following should
        self.assertEqual(
            admissions.get().type,
            AdmissionType.get_value(self.update_data["type_select"]),
        )
        self.assertEqual(
            admissions.get().candidate.pk, self.update_data["candidate_write"]
        )
        self.assertEqual(admissions.get().comment, self.update_data["comment"])
