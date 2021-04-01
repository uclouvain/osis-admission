from django.test import TestCase
from django.urls import reverse

from admission.contrib.models import AdmissionType, AdmissionDoctorate
from base.tests.factories.person import PersonFactory


class AdmissionDoctorateApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = PersonFactory()
        cls.candidate = PersonFactory()
        cls.create_data = {
            "type_select": AdmissionType.PRE_ADMISSION.name,
            "candidate_write": cls.candidate.pk,
            "comment": "test admission doctorate serializer",
        }
        cls.update_data = {
            "type_select": AdmissionType.ADMISSION.name,
            "candidate_write": cls.candidate.pk,
            "comment": "test admission doctorate serializer",
        }
        cls.create_url = reverse("admissions:doctorate-api-list")

    def test_admission_doctorate_creation_using_api(self):
        self.client.force_login(self.author.user)
        response = self.client.post(self.create_url, data=self.create_data)
        self.assertEqual(response.status_code, 201)
        admissions = AdmissionDoctorate.objects.all()
        self.assertEqual(admissions.count(), 1)
        self.assertEqual(admissions.get().author, self.author)
        self.assertEqual(admissions.get().candidate, self.candidate)
        self.assertEqual(admissions.get().comment, self.create_data["comment"])
