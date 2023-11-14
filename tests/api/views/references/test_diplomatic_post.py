# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd import BE_ISO_CODE, FR_ISO_CODE, EN_ISO_CODE
from admission.tests.factories.diplomatic_post import DiplomaticPostFactory
from base.tests.factories.person import PersonFactory
from reference.tests.factories.country import CountryFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class RetrieveDiplomaticPostViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.be_country = CountryFactory(iso_code=BE_ISO_CODE)
        cls.fr_country = CountryFactory(iso_code=FR_ISO_CODE)
        cls.en_country = CountryFactory(iso_code=EN_ISO_CODE)

    def setUp(self):
        self.user = PersonFactory().user
        self.diplomatic_post = DiplomaticPostFactory(
            name_fr='Bruxelles',
            name_en='Brussels',
            email='bruxelles@example.com',
        )
        self.diplomatic_post.countries.add(self.be_country)
        self.diplomatic_post.countries.add(self.en_country)
        self.url = reverse('retrieve-diplomatic-post', kwargs={'code': self.diplomatic_post.code})

    def test_retrieve_diplomatic_post(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertEqual(result['name_fr'], self.diplomatic_post.name_fr)
        self.assertEqual(result['name_en'], self.diplomatic_post.name_en)
        self.assertEqual(result['email'], self.diplomatic_post.email)
        self.assertEqual(result['code'], self.diplomatic_post.code)
        self.assertCountEqual(result['countries_iso_codes'], [BE_ISO_CODE, EN_ISO_CODE])
