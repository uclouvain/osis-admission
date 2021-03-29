from django.test import TestCase
from django.urls import reverse

from admission.contrib.models import AdmissionDoctorate, AdmissionType
from base.tests.factories.person import PersonFactory


class AdmissionDoctorateCreateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.candidate = PersonFactory()
        cls.url = reverse("admissions:doctorate-create")
        cls.data = {
            "comment": "this is a test",
            "type": AdmissionType.ADMISSION.name,
            "candidate": cls.candidate.id,
        }

    def test_create_doctorate_admission_add_user_as_author(self):
        self.client.force_login(self.person.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertEqual(response.status_code, 200)
        # check that the object in the response got the person as author
        self.assertEqual(response.context_data["object"].author, self.person)
        # and double check by getting it from the db
        admission_author = AdmissionDoctorate.objects.get(
            candidate=self.candidate.id
        ).author
        self.assertEqual(admission_author, self.person)

    def test_create_doctorate_admission_redirect_to_detail_view(self):
        self.client.force_login(self.person.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertEqual(response.status_code, 200)
        # make sure that the AdmissionDoctorate creation redirect to the detail view
        self.assertTemplateUsed(
            response,
            "admission/doctorate/admission_doctorate_detail.html",
        )

    def test_view_context_data_contains_cancel_url(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["cancel_url"], reverse("admissions:doctorate-list")
        )
