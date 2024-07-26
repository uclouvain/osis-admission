# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from admission.models import DiplomaticPost
from admission.ddd import FR_ISO_CODE, EN_ISO_CODE
from admission.tests.factories.diplomatic_post import DiplomaticPostFactory
from base.tests.factories.person import PersonFactory
from osis_profile import BE_ISO_CODE
from reference.tests.factories.country import CountryFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class AutocompleteDiplomaticPostViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.be_country = CountryFactory(iso_code=BE_ISO_CODE)
        cls.fr_country = CountryFactory(iso_code=FR_ISO_CODE)
        cls.en_country = CountryFactory(iso_code=EN_ISO_CODE)
        cls.url = reverse('autocomplete-diplomatic-post')
        DiplomaticPost.objects.all().delete()

    def setUp(self):
        self.user = PersonFactory().user
        self.diplomatic_posts = [
            DiplomaticPostFactory(name_fr='Bruxelles', name_en='Brussels', email='bruxelles@example.com'),
            DiplomaticPostFactory(name_fr='Bruges', name_en='Bruges', email='bruges@example.com'),
            DiplomaticPostFactory(name_fr='Strasbourg', name_en='Strasbourg', email='strasbourg@example.com'),
            DiplomaticPostFactory(name_fr='Paris', name_en='Paris', email='paris@example.com'),
            DiplomaticPostFactory(name_fr='Londres', name_en='London', email='londres@example.com'),
        ]
        self.diplomatic_posts[0].countries.add(self.be_country)
        self.diplomatic_posts[1].countries.add(self.en_country)
        self.diplomatic_posts[1].countries.add(self.be_country)
        self.diplomatic_posts[2].countries.add(self.fr_country)
        self.diplomatic_posts[3].countries.add(self.fr_country)
        self.diplomatic_posts[4].countries.add(self.en_country)

    def test_diplomatic_post_autocomplete_without_params(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        results = response.json()
        self.assertEqual(results['count'], len(self.diplomatic_posts))

        results = results['results']

        self.assertEqual(results[0]['name_fr'], self.diplomatic_posts[1].name_fr)
        self.assertEqual(results[0]['name_en'], self.diplomatic_posts[1].name_en)
        self.assertEqual(results[0]['email'], self.diplomatic_posts[1].email)
        self.assertEqual(results[0]['code'], self.diplomatic_posts[1].code)
        self.assertCountEqual(results[0]['countries_iso_codes'], [BE_ISO_CODE, EN_ISO_CODE])

        self.assertEqual(results[1]['code'], self.diplomatic_posts[0].code)
        self.assertEqual(results[2]['code'], self.diplomatic_posts[4].code)
        self.assertEqual(results[3]['code'], self.diplomatic_posts[3].code)
        self.assertEqual(results[4]['code'], self.diplomatic_posts[2].code)

    def test_diplomatic_post_autocomplete_with_search_param(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url + '?search=Bruxelles')
        self.assertEqual(response.status_code, 200)

        results = response.json()
        self.assertEqual(results['count'], 1)

        results = results['results']

        self.assertEqual(results[0]['code'], self.diplomatic_posts[0].code)

    def test_diplomatic_post_autocomplete_with_country_param(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url + f'?country={FR_ISO_CODE}')
        self.assertEqual(response.status_code, 200)

        results = response.json()
        self.assertEqual(results['count'], len(self.diplomatic_posts))

        results = results['results']

        # French diplomatic posts are returned first
        self.assertEqual(results[0]['code'], self.diplomatic_posts[3].code)
        self.assertEqual(results[1]['code'], self.diplomatic_posts[2].code)

        # The other diplomatic posts are returned in alphabetical order
        self.assertEqual(results[2]['code'], self.diplomatic_posts[1].code)
        self.assertEqual(results[3]['code'], self.diplomatic_posts[0].code)
        self.assertEqual(results[4]['code'], self.diplomatic_posts[4].code)
