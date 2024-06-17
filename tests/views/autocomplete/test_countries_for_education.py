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

from django.contrib.auth.models import User, AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse

from admission.views.autocomplete.countries_for_education import CountriesAutocompleteForEducation
from osis_profile.models.enums.education import ForeignDiplomaTypes
from reference.tests.factories.country import CountryFactory


class CountriesForEducationAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()

        # Mocked data
        cls.be_country = CountryFactory(
            iso_code='BE',
            name='Belgique',
            name_en='Belgium',
            active=True,
            european_union=True,
        )
        cls.fr_country = CountryFactory(
            iso_code='FR',
            name='France',
            name_en='France',
            active=True,
            european_union=True,
        )
        cls.former_country = CountryFactory(
            iso_code='FC',
            name='Ancien pays',
            name_en='Former country',
            active=False,
            european_union=False,
        )

        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )

        cls.url = reverse('admission:autocomplete:countries-for-education')

    def test_promoters_redirects_with_anonymous_user(self):
        request = self.factory.get(self.url)
        request.user = AnonymousUser()

        response = CountriesAutocompleteForEducation.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_countries_without_foreign_diploma_type(self):
        request = self.factory.get(self.url)
        request.user = self.user

        response = CountriesAutocompleteForEducation.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    {
                        'id': self.former_country.pk,
                        'text': 'Ancien pays',
                        'selected_text': 'Ancien pays',
                        'european_union': False,
                    },
                    {
                        'id': self.fr_country.pk,
                        'text': 'France',
                        'selected_text': 'France',
                        'european_union': True,
                    },
                ],
            },
        )

    def test_countries_with_national_diploma(self):
        request = self.factory.get(
            self.url,
            data={
                'forward': json.dumps({'foreign_diploma_type': ForeignDiplomaTypes.NATIONAL_BACHELOR.name}),
            },
        )
        request.user = self.user

        response = CountriesAutocompleteForEducation.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    {
                        'id': self.former_country.pk,
                        'text': 'Ancien pays',
                        'selected_text': 'Ancien pays',
                        'european_union': False,
                    },
                    {
                        'id': self.fr_country.pk,
                        'text': 'France',
                        'selected_text': 'France',
                        'european_union': True,
                    },
                ],
            },
        )

    def test_countries_with_international_diploma(self):
        request = self.factory.get(
            self.url,
            data={
                'forward': json.dumps({'foreign_diploma_type': ForeignDiplomaTypes.INTERNATIONAL_BACCALAUREATE.name}),
            },
        )
        request.user = self.user

        response = CountriesAutocompleteForEducation.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    {
                        'id': self.former_country.pk,
                        'text': 'Ancien pays',
                        'selected_text': 'Ancien pays',
                        'european_union': False,
                    },
                    {
                        'id': self.be_country.pk,
                        'text': 'Belgique',
                        'selected_text': 'Belgique',
                        'european_union': True,
                    },
                    {
                        'id': self.fr_country.pk,
                        'text': 'France',
                        'selected_text': 'France',
                        'european_union': True,
                    },
                ],
            },
        )

    def test_countries_with_european_diploma(self):
        request = self.factory.get(
            self.url,
            data={
                'forward': json.dumps({'foreign_diploma_type': ForeignDiplomaTypes.EUROPEAN_BACHELOR.name}),
            },
        )
        request.user = self.user

        response = CountriesAutocompleteForEducation.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    {
                        'id': self.former_country.pk,
                        'text': 'Ancien pays',
                        'selected_text': 'Ancien pays',
                        'european_union': False,
                    },
                    {
                        'id': self.be_country.pk,
                        'text': 'Belgique',
                        'selected_text': 'Belgique',
                        'european_union': True,
                    },
                    {
                        'id': self.fr_country.pk,
                        'text': 'France',
                        'selected_text': 'France',
                        'european_union': True,
                    },
                ],
            },
        )
