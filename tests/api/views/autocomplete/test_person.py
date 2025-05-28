# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework.test import APITestCase

from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.user import UserFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class PersonAutocompleteTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_autocomplete_persons(self):
        self.client.force_authenticate(user=self.user)
        PersonFactory(first_name="Jean-Marc", global_id="00005789")
        response = self.client.get(
            resolve_url('autocomplete-person') + '?search=jean',
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 1)
        response = self.client.get(
            resolve_url('autocomplete-person') + '?search=57',
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 1)

    def test_autocomplete_persons_depending_on_roles(self):
        self.client.force_authenticate(user=self.user)

        url = resolve_url('autocomplete-person') + '?search=5789'

        person = PersonFactory(global_id="00005789")

        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 1)

        student = StudentFactory(person=person)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 0)

        tutor = TutorFactory(person=person)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 1)
