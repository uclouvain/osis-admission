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

from django.utils import translation

from django.contrib.auth.models import User, AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse

from admission.views.autocomplete.countries import CountriesAutocomplete
from reference.tests.factories.country import CountryFactory


class CountriesAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()

        # Mocked data
        cls.be_country = CountryFactory(
            iso_code='BE',
            name='Belgique',
            name_en='Belgium',
            active=True,
        )
        cls.fr_country = CountryFactory(
            iso_code='FR',
            name='France',
            name_en='France',
            active=True,
        )
        cls.former_country = CountryFactory(
            iso_code='FC',
            name='Ancien pays',
            name_en='Former country',
            active=False,
        )

        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )

    def test_promoters_redirects_with_anonymous_user(self):
        request = self.factory.get(reverse('admission:autocomplete:countries'))
        request.user = AnonymousUser()

        response = CountriesAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_countries_without_query(self):
        request = self.factory.get(reverse('admission:autocomplete:countries'))
        request.user = self.user

        response = CountriesAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    {'id': self.former_country.pk, 'text': 'Ancien pays', 'selected_text': 'Ancien pays'},
                    {'id': self.be_country.pk, 'text': 'Belgique', 'selected_text': 'Belgique'},
                    {'id': self.fr_country.pk, 'text': 'France', 'selected_text': 'France'},
                ],
            },
        )

    def test_countries_with_iso_code(self):
        request = self.factory.get(
            reverse('admission:autocomplete:countries'),
            data={
                'forward': json.dumps({'id_field': 'iso_code'}),
            },
        )
        request.user = self.user

        response = CountriesAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    {'id': self.former_country.iso_code, 'text': 'Ancien pays', 'selected_text': 'Ancien pays'},
                    {'id': self.be_country.iso_code, 'text': 'Belgique', 'selected_text': 'Belgique'},
                    {'id': self.fr_country.iso_code, 'text': 'France', 'selected_text': 'France'},
                ],
            },
        )

    def test_countries_only_active(self):
        request = self.factory.get(
            reverse('admission:autocomplete:countries'),
            data={
                'forward': json.dumps({'active': True}),
            },
        )
        request.user = self.user

        response = CountriesAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    {'id': self.be_country.pk, 'text': 'Belgique', 'selected_text': 'Belgique'},
                    {'id': self.fr_country.pk, 'text': 'France', 'selected_text': 'France'},
                ],
            },
        )

    def test_countries_only_inactive(self):
        request = self.factory.get(
            reverse('admission:autocomplete:countries'),
            data={
                'forward': json.dumps({'active': False}),
            },
        )
        request.user = self.user

        response = CountriesAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    {'id': self.former_country.pk, 'text': 'Ancien pays', 'selected_text': 'Ancien pays'},
                ],
            },
        )

    def test_countries_with_query(self):
        request = self.factory.get(
            reverse('admission:autocomplete:countries'),
            data={
                'q': 'bel',
            },
        )
        request.user = self.user

        response = CountriesAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    {'id': self.be_country.pk, 'text': 'Belgique', 'selected_text': 'Belgique'},
                ],
            },
        )

    def test_countries_with_query_other_language(self):
        request = self.factory.get(
            reverse('admission:autocomplete:countries'),
            data={
                'q': 'bel',
            },
        )

        request.user = self.user

        with translation.override('en'):
            response = CountriesAutocomplete.as_view()(request)

            self.assertEqual(response.status_code, 200)
            self.assertJSONEqual(
                response.content,
                {
                    'pagination': {'more': False},
                    'results': [
                        {'id': self.be_country.pk, 'text': 'Belgium', 'selected_text': 'Belgium'},
                    ],
                },
            )
