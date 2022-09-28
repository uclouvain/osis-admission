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

from base.models.enums import organization_type
from base.tests.factories.campus import CampusFactory
from base.tests.factories.organization import MainOrganizationFactory
from base.tests.factories.user import UserFactory


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class CampusReferenceTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.campuses = [
            CampusFactory(name="Paris", organization__type=organization_type.ACADEMIC_PARTNER),
            CampusFactory(name="Nantes", organization__type=organization_type.ACADEMIC_PARTNER),
            CampusFactory(name="Louvain-la-Neuve", organization=MainOrganizationFactory()),
            CampusFactory(name="Bruxelles Woluwe", organization=MainOrganizationFactory()),
        ]
        cls.user = UserFactory()

    def test_retrieve_campus_if_valid_uuid(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('retrieve-campus', uuid=str(self.campuses[2].uuid)),
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'name': self.campuses[2].name, 'uuid': str(self.campuses[2].uuid)})

    def test_return_404_if_unknown_uuid(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('retrieve-campus', uuid=str(uuid.uuid4())),
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_list_campuses(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('list-campuses'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()),  2)
        self.assertEqual(response.json(), [
            {'name': self.campuses[3].name, 'uuid': str(self.campuses[3].uuid)},
            {'name': self.campuses[2].name, 'uuid': str(self.campuses[2].uuid)},
        ])
