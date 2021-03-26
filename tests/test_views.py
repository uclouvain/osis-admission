from django.test import TestCase
from django.urls import reverse

from admission.contrib.models import AdmissionDoctorate, AdmissionType
from admission.contrib.views.autocomplete import PersonAutocomplete
from admission.tests.factories import AdmissionDoctorateFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory


class PersonAutocompleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.author = PersonFactory(user=cls.user)
        cls.candidate = PersonFactory(email="foo@bar.example.org")
        cls.url = reverse("admissions:person_autocomplete")

    def test_filter_autocomplete_doesnt_return_candidates_with_no_admissions(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, data={"q": self.candidate.email})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 0)

    def test_filter_autocomplete_returns_candidates_with_admissions(self):
        self.client.force_login(self.user)
        AdmissionDoctorateFactory(candidate=self.candidate, author=self.author)
        response = self.client.get(self.url, data={"q": "bar"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["id"], str(self.candidate.id))
        self.assertEqual(
            data["results"][0]["text"],
            PersonAutocomplete().get_result_label(self.candidate),
        )


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
