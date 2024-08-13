# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test.utils import override_settings
from django.urls import reverse

from reference.tests.factories.language import LanguageFactory


class LanguageAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()

        # Mocked data
        cls.fr_language = LanguageFactory(
            name='Français',
            name_en='French',
            code='FR',
        )

        cls.en_language = LanguageFactory(
            name='Anglais',
            name_en='English',
            code='EN',
        )

        cls.es_language = LanguageFactory(
            name='Espagnol',
            name_en='Spanish',
            code='ES',
        )

        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )

        cls.url = reverse('admission:autocomplete:language')

    @override_settings(LANGUAGE_CODE='fr-be')
    def test_retrieve_languages_in_french(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        json_response = response.json()

        self.assertEqual(
            json_response,
            {
                'pagination': {'more': False},
                'results': [
                    {
                        'id': language.code,
                        'text': language.name,
                        'selected_text': language.name,
                    }
                    for language in [
                        self.en_language,
                        self.es_language,
                        self.fr_language,
                    ]
                ],
            },
        )

    @override_settings(LANGUAGE_CODE='fr-be')
    def test_retrieve_languages_with_their_id_instead_of_their_language_code(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            {
                'forward': json.dumps({'id_field': 'id'}),
            },
        )

        self.assertEqual(response.status_code, 200)

        json_response = response.json()

        self.assertEqual(
            json_response,
            {
                'pagination': {'more': False},
                'results': [
                    {
                        'id': language.id,
                        'text': language.name,
                        'selected_text': language.name,
                    }
                    for language in [
                        self.en_language,
                        self.es_language,
                        self.fr_language,
                    ]
                ],
            },
        )

    @override_settings(LANGUAGE_CODE='en')
    def test_retrieve_languages_in_english(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        json_response = response.json()

        self.assertEqual(
            json_response,
            {
                'pagination': {'more': False},
                'results': [
                    {
                        'id': language.code,
                        'text': language.name_en,
                        'selected_text': language.name_en,
                    }
                    for language in [
                        self.en_language,
                        self.fr_language,
                        self.es_language,
                    ]
                ],
            },
        )

    @override_settings(LANGUAGE_CODE='fr-be')
    def test_search_languages_in_french(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            data={
                'q': 'espag',
            },
        )

        self.assertEqual(response.status_code, 200)

        json_response = response.json()

        (
            self.assertEqual(
                json_response,
                {
                    'pagination': {'more': False},
                    'results': [
                        {
                            'id': language.code,
                            'text': language.name,
                            'selected_text': language.name,
                        }
                        for language in [
                            self.es_language,
                        ]
                    ],
                },
            )
        )

    @override_settings(LANGUAGE_CODE='en')
    def test_search_languages_in_english(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            data={
                'q': 'span',
            },
        )

        self.assertEqual(response.status_code, 200)

        json_response = response.json()

        self.assertEqual(
            json_response,
            {
                'pagination': {'more': False},
                'results': [
                    {
                        'id': language.code,
                        'text': language.name_en,
                        'selected_text': language.name_en,
                    }
                    for language in [
                        self.es_language,
                    ]
                ],
            },
        )
