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

from admission.contrib.views.autocomplete import PersonAutocomplete
from admission.tests.factories import DoctorateAdmissionFactory
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
        DoctorateAdmissionFactory(candidate=self.candidate, author=self.author)
        response = self.client.get(self.url, data={"q": "bar"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["id"], str(self.candidate.id))
        self.assertEqual(
            data["results"][0]["text"],
            PersonAutocomplete().get_result_label(self.candidate),
        )
