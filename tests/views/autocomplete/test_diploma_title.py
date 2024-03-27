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
from django.urls import reverse

from reference.models.diploma_title import mapping_study_cycle
from reference.models.enums.study_type import StudyType
from reference.tests.factories.diploma_title import DiplomaTitleFactory


class DiplomaTitleAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()

        univ_prefix = mapping_study_cycle[StudyType.UNIVERSITY.name] + ' - '
        snu_prefix = mapping_study_cycle[StudyType.NON_UNIVERSITY.name] + ' - '

        cls.data = {
            'forward': json.dumps({'display_study_type': True}),
        }

        # Mocked data
        not_active_diploma_title = DiplomaTitleFactory(
            active=False,
            title='Bachelier inactif',
            study_type=StudyType.UNIVERSITY.name,
        )
        master_title = DiplomaTitleFactory(
            active=True,
            title='Master informatique',
            study_type=StudyType.UNIVERSITY.name,
        )
        bachelor_title = DiplomaTitleFactory(
            active=True,
            title='Bachelor informatique à Louvain',
            study_type=StudyType.UNIVERSITY.name,
        )
        politic_title = DiplomaTitleFactory(
            active=True,
            title='Politique',
            study_type=StudyType.NON_UNIVERSITY.name,
        )

        cls.not_active_diploma_data = {
            'id': str(not_active_diploma_title.pk),
            'text': univ_prefix + not_active_diploma_title.title,
            'selected_text': univ_prefix + not_active_diploma_title.title,
            'cycle': not_active_diploma_title.cycle,
        }

        cls.master_title_data = {
            'id': str(master_title.pk),
            'text': univ_prefix + master_title.title,
            'selected_text': univ_prefix + master_title.title,
            'cycle': master_title.cycle,
        }

        cls.bachelor_title_data = {
            'id': str(bachelor_title.pk),
            'text': univ_prefix + bachelor_title.title,
            'selected_text': univ_prefix + bachelor_title.title,
            'cycle': bachelor_title.cycle,
        }

        cls.politic_title_data = {
            'id': str(politic_title.pk),
            'text': snu_prefix + politic_title.title,
            'selected_text': snu_prefix + politic_title.title,
            'cycle': politic_title.cycle,
        }

        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )

        cls.url = reverse('admission:autocomplete:diploma-title')

    def test_retrieve_all_active_diploma_titles(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            data={
                'forward': json.dumps(
                    {
                        'display_study_type': True,
                    },
                ),
            },
        )

        self.assertEqual(response.status_code, 200)

        json_response = response.json()

        self.assertEqual(
            json_response,
            {
                'pagination': {'more': False},
                'results': [
                    self.bachelor_title_data,
                    self.master_title_data,
                    self.politic_title_data,
                ],
            },
        )

    def test_retrieve_specific_study_type_diploma_titles(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            data={
                'forward': json.dumps(
                    {
                        'study_type': StudyType.NON_UNIVERSITY.name,
                        'display_study_type': True,
                    },
                ),
            },
        )

        self.assertEqual(response.status_code, 200)

        json_response = response.json()

        self.assertEqual(
            json_response,
            {
                'pagination': {'more': False},
                'results': [
                    self.politic_title_data,
                ],
            },
        )

    def test_retrieve_specific_diploma_titles_by_title(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            data={
                'q': 'à louvain',
                'forward': json.dumps(
                    {
                        'display_study_type': True,
                    },
                ),
            },
        )

        self.assertEqual(response.status_code, 200)

        json_response = response.json()

        self.assertEqual(
            json_response,
            {
                'pagination': {'more': False},
                'results': [
                    self.bachelor_title_data,
                ],
            },
        )
