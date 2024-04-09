# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import json

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from osis_profile import BE_ISO_CODE
from reference.tests.factories.city import ZipCodeFactory
from reference.tests.factories.country import CountryFactory


class CitiesAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()

        # Mocked data
        belgian_country = CountryFactory(
            iso_code=BE_ISO_CODE,
            name='Belgique',
            name_en='Belgium',
        )

        ZipCodeFactory(
            zip_code='1348',
            municipality='Louvain-la-Neuve',
            country=belgian_country,
        )

        ZipCodeFactory(
            zip_code='1000',
            municipality='Bruxelles',
            country=belgian_country,
        )

        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )

        cls.url = reverse('admission:autocomplete:cities')

    def test_cities_without_query_and_postal_code(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                'pagination': {'more': False},
                'results': [
                    {'id': 'Bruxelles', 'text': 'Bruxelles'},
                    {'id': 'Louvain-la-Neuve', 'text': 'Louvain-la-Neuve'},
                ],
            },
        )

    def test_cities_with_query_but_no_postal_code(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            {
                'q': 'louvain',
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                'pagination': {'more': False},
                'results': [
                    {'id': 'Louvain-la-Neuve', 'text': 'Louvain-la-Neuve'},
                ],
            },
        )

    def test_cities_with_postal_code_but_no_query(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            {
                'forward': json.dumps({'postal_code': '1348'}),
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                'pagination': {'more': False},
                'results': [
                    {'id': 'Louvain-la-Neuve', 'text': 'Louvain-la-Neuve'},
                ],
            },
        )

    def test_cities_with_postal_code_and_query(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            {
                'forward': json.dumps({'postal_code': '1348'}),
                'q': 'louvain',
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                'pagination': {'more': False},
                'results': [
                    {'id': 'Louvain-la-Neuve', 'text': 'Louvain-la-Neuve'},
                ],
            },
        )

        response = self.client.get(
            self.url,
            {
                'forward': json.dumps({'postal_code': '1348'}),
                'q': 'bruxelles',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                'pagination': {'more': False},
                'results': [],
            },
        )
