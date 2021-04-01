from django.test import TestCase
from django.urls import reverse

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
        cls.url = reverse("admissions:person-autocomplete")

    def test_filter_autocomplete_returns_all_persons(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, data={"q": self.candidate.email})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)


class CandidateAutocompleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.author = PersonFactory(user=cls.user)
        cls.candidate = PersonFactory(email="foo@bar.example.org")
        cls.url = reverse("admissions:candidate-autocomplete")

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
