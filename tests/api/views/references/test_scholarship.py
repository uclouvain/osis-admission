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
import uuid

from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework.test import APITestCase

from admission.tests.factories.scholarship import DoubleDegreeScholarshipFactory
from base.tests.factories.user import UserFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class ScholarshipReferenceTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.scholarships = [
            DoubleDegreeScholarshipFactory(short_name='DDS-1', long_name='Double degree scholarship 1'),
            DoubleDegreeScholarshipFactory(short_name='DDS-2', long_name='Double degree scholarship 2'),
        ]
        cls.user = UserFactory()

    def test_retrieve_scholarship_if_valid_uuid(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('retrieve-scholarship', uuid=str(self.scholarships[0].uuid)),
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'uuid': str(self.scholarships[0].uuid),
            'short_name': self.scholarships[0].short_name,
            'long_name': self.scholarships[0].long_name,
            'type': self.scholarships[0].type,
        })

    def test_return_404_if_unknown_uuid(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('retrieve-scholarship', uuid=str(uuid.uuid4())),
            format='json',
        )
        self.assertEqual(response.status_code, 404)
