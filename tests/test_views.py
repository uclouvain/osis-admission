from django.test import TestCase
from django.urls import reverse

from admission.contrib.views.autocomplete import PersonAutocomplete
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory


class PersonAutocompleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.candidate = PersonFactory()
        cls.url = reverse("admissions:person_autocomplete")

    def test_filter_autocomplete_returns_existing_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, data={"q": self.candidate.email})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["id"], str(self.candidate.id))
        self.assertEqual(
            data["results"][0]["text"],
            PersonAutocomplete().get_result_label(self.candidate),
        )
