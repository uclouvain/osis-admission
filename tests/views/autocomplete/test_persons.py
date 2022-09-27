# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.auth.models import User, AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse

from admission.tests.factories.roles import CandidateFactory
from admission.tests.factories.supervision import PromoterFactory
from admission.views.autocomplete.persons import CandidatesAutocomplete, PromotersAutocomplete
from base.models.person import Person
from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory


class PersonsAutocompleteTestCase(TestCase):
    first_candidate = None
    second_candidate = None
    first_promoter = None

    @classmethod
    def _formatted_person_result(cls, p: Person):
        return {
            'id': p.global_id,
            'text': '{}, {}'.format(p.last_name, p.first_name),
        }

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )
        # Create candidates
        cls.first_candidate = CandidateFactory(
            person=PersonFactory(
                first_name='John',
                last_name='Doe',
            )
        ).person
        StudentFactory(
            person=cls.first_candidate,
            registration_id='0001',
        )
        cls.second_candidate = CandidateFactory(
            person=PersonFactory(
                first_name='Jane',
                last_name='Poe',
            )
        ).person
        StudentFactory(person=cls.second_candidate, registration_id='0002')

        # Create promoters
        cls.first_promoter = PromoterFactory().person

    def test_candidates_redirects_with_anonymous_user(self):
        request = self.factory.get(reverse('admission:autocomplete:candidates'))
        request.user = AnonymousUser()

        response = CandidatesAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_candidates_without_query(self):
        request = self.factory.get(reverse('admission:autocomplete:candidates'))
        request.user = self.user

        response = CandidatesAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [],
            },
        )

    def test_candidates_with_name(self):
        request = self.factory.get(reverse('admission:autocomplete:candidates'), data={'q': 'oe'})
        request.user = self.user

        response = CandidatesAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.first_candidate),
                    self._formatted_person_result(self.second_candidate),
                ],
            },
        )

    def test_candidates_with_registration_id(self):
        request = self.factory.get(
            reverse('admission:autocomplete:candidates'),
            data={
                'q': '0001',
            },
        )
        request.user = self.user

        response = CandidatesAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.first_candidate),
                ],
            },
        )

    def test_promoters_redirects_with_anonymous_user(self):
        request = self.factory.get(reverse('admission:autocomplete:candidates'))
        request.user = AnonymousUser()

        response = CandidatesAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_promoters_without_query(self):
        request = self.factory.get(reverse('admission:autocomplete:promoters'))
        request.user = self.user

        response = PromotersAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [],
            },
        )

    def test_promoters_with_name(self):
        request = self.factory.get(
            reverse('admission:autocomplete:promoters'),
            data={
                'q': self.first_promoter.first_name,
            },
        )
        request.user = self.user

        response = PromotersAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.first_promoter),
                ],
            },
        )
