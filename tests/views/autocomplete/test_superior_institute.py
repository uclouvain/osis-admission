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

import freezegun
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from base.tests.factories.entity_version_address import EntityVersionAddressFactory
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.superior_non_university import SuperiorNonUniversityFactory
from reference.tests.factories.university import UniversityFactory


@freezegun.freeze_time('2023-01-01')
class SuperiorInstituteAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()

        # Mocked data
        be_country = CountryFactory(name='Belgium', iso_code='BE')
        fr_country = CountryFactory(name='France', iso_code='FR')

        first_university = UniversityFactory(
            name='Université catholique de Louvain',
            acronym='UCL',
        )
        first_university_address = EntityVersionAddressFactory(
            entity_version__entity__organization=first_university,
            city='Louvain-la-Neuve',
            street='Place de la République',
            street_number='1',
            postal_code='1348',
            country=be_country,
            entity_version__parent=None,
        )
        cls.first_university_data = {
            'id': first_university.id,
            'text': (
                'Université catholique de Louvain <span class="school-address">'
                'Place de la République 1, 1348 Louvain-la-Neuve</span>'
            ),
            'community': first_university.community,
        }

        second_university = UniversityFactory(
            name='Université de Mons',
            acronym='UM',
        )
        second_university_address = EntityVersionAddressFactory(
            entity_version__entity__organization=second_university,
            city='Mons',
            street='Rue de l’Université',
            street_number='2',
            postal_code='7000',
            country=be_country,
            entity_version__parent=None,
        )
        cls.second_university_data = {
            'id': second_university.id,
            'text': 'Université de Mons <span class="school-address">Rue de l’Université 2, 7000 Mons</span>',
            'community': second_university.community,
        }

        third_university = UniversityFactory(
            name='Université de Lille',
            acronym='UL',
        )
        third_university_address = EntityVersionAddressFactory(
            entity_version__entity__organization=third_university,
            city='Lille',
            street='Place du marché',
            street_number='3',
            postal_code='59000',
            country=fr_country,
            entity_version__parent=None,
        )
        cls.third_university_data = {
            'id': third_university.id,
            'text': 'Université de Lille <span class="school-address">Place du marché 3, 59000 Lille</span>',
            'community': third_university.community,
        }

        first_superior_non_university = SuperiorNonUniversityFactory(
            name='Ecole de commerce',
            acronym='EC',
        )
        first_superior_non_university_address = EntityVersionAddressFactory(
            entity_version__entity__organization=first_superior_non_university,
            city='Bruxelles',
            street='Boulevard du triomphe',
            street_number='4',
            postal_code='1000',
            country=be_country,
            entity_version__parent=None,
        )
        cls.first_superior_non_university_data = {
            'id': first_superior_non_university.id,
            'text': 'Ecole de commerce <span class="school-address">Boulevard du triomphe 4, 1000 Bruxelles</span>',
            'community': first_superior_non_university.community,
        }

        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )

        cls.url = reverse('admission:autocomplete:superior-institute')

    def test_retrieve_institutes_by_country(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            data={'forward': json.dumps({'country': 'FR'})},
        )

        self.assertEqual(response.status_code, 200)

        json_response = response.json()

        self.assertEqual(len(json_response['results']), 1)

        self.assertEqual(
            json_response,
            {
                'pagination': {'more': False},
                'results': [self.third_university_data],
            },
        )

    def test_retrieve_institutes_by_zip_code(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url, data={'q': '1348'})

        self.assertEqual(response.status_code, 200)

        json_response = response.json()

        self.assertEqual(len(json_response['results']), 1)

        self.assertEqual(
            json_response,
            {
                'pagination': {'more': False},
                'results': [self.first_university_data],
            },
        )

    def test_retrieve_institutes_by_city(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url, data={'q': 'bruxelles'})

        self.assertEqual(response.status_code, 200)

        json_response = response.json()

        self.assertEqual(len(json_response['results']), 1)

        self.assertEqual(
            json_response,
            {
                'pagination': {'more': False},
                'results': [self.first_superior_non_university_data],
            },
        )

    def test_retrieve_institutes_by_acronym(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url, data={'q': 'UM'})

        self.assertEqual(response.status_code, 200)

        json_response = response.json()

        self.assertEqual(len(json_response['results']), 1)

        self.assertEqual(
            json_response,
            {
                'pagination': {'more': False},
                'results': [self.second_university_data],
            },
        )
