# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from admission.views.autocomplete.entities import EntityAutocomplete
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import EntityType
from base.models.enums.organization_type import ACADEMIC_PARTNER, MAIN
from base.tests.factories.entity_version import EntityVersionFactory


class EntityAutocompleteTestCase(TestCase):
    @classmethod
    def _formatted_entity_result(cls, entity: EntityVersion):
        return {
            'id': str(entity.uuid),
            'text': '{} ({})'.format(entity.title, entity.acronym),
            'selected_text': '{} ({})'.format(entity.title, entity.acronym),
        }

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )
        EntityVersion.objects.all().delete()
        cls.first_ucl_institute = EntityVersionFactory(
            entity_type=EntityType.INSTITUTE.name,
            entity__organization__type=MAIN,
            acronym='I1',
            title='Institute 1',
        )
        cls.second_ucl_institute = EntityVersionFactory(
            entity_type=EntityType.INSTITUTE.name,
            entity__organization__type=MAIN,
            acronym='I2',
            title='Institute 2',
        )
        cls.other_organization_institute = EntityVersionFactory(
            entity_type=EntityType.INSTITUTE.name,
            entity__organization__type=ACADEMIC_PARTNER,
            acronym='I3',
            title='Institute 3',
        )
        cls.ucl_school = EntityVersionFactory(
            entity_type=EntityType.SCHOOL.name,
            entity__organization__type=MAIN,
            acronym='S1',
            title='School 1',
        )
        cls.other_organization_school = EntityVersionFactory(
            entity_type=EntityType.SCHOOL.name,
            entity__organization__type=ACADEMIC_PARTNER,
            acronym='S2',
            title='School 2',
        )

        cls.url = reverse('admission:autocomplete:entities')

    def test_redirects_with_anonymous_user(self):
        request = self.factory.get(self.url)
        request.user = AnonymousUser()

        response = EntityAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_without_query(self):
        request = self.factory.get(self.url)
        request.user = self.user

        response = EntityAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_entity_result(self.first_ucl_institute),
                    self._formatted_entity_result(self.second_ucl_institute),
                    self._formatted_entity_result(self.other_organization_institute),
                    self._formatted_entity_result(self.ucl_school),
                    self._formatted_entity_result(self.other_organization_school),
                ],
            },
        )

    def test_filter_by_entity_type(self):
        request = self.factory.get(self.url, data={'forward': json.dumps({'entity_type': EntityType.INSTITUTE.name})})
        request.user = self.user

        response = EntityAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_entity_result(self.first_ucl_institute),
                    self._formatted_entity_result(self.second_ucl_institute),
                    self._formatted_entity_result(self.other_organization_institute),
                ],
            },
        )

    def test_filter_by_organization_type(self):
        request = self.factory.get(self.url, data={'forward': json.dumps({'organization_type': MAIN})})
        request.user = self.user

        response = EntityAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_entity_result(self.first_ucl_institute),
                    self._formatted_entity_result(self.second_ucl_institute),
                    self._formatted_entity_result(self.ucl_school),
                ],
            },
        )

    def test_filter_by_acronym(self):
        request = self.factory.get(self.url, data={'q': 'I1'})
        request.user = self.user

        response = EntityAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_entity_result(self.first_ucl_institute),
                ],
            },
        )

    def test_filter_by_title(self):
        request = self.factory.get(self.url, data={'q': 'School'})
        request.user = self.user

        response = EntityAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_entity_result(self.ucl_school),
                    self._formatted_entity_result(self.other_organization_school),
                ],
            },
        )
