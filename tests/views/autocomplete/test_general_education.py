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
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse

from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.education_group_year import EducationGroupYearFactory


@freezegun.freeze_time('2023-01-01')
class GeneralEducationAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()

        AdmissionAcademicCalendarFactory.produce_all_required()

        EducationGroupYearFactory(
            acronym='FOOBAR',
            title='wegweij wegioj egewgeg',
            academic_year__year=2023,
            education_group_type__name=TrainingType.BACHELOR.name,
        )

        EducationGroupYearFactory(
            acronym='FOOBAR',
            title='wegweij wegioj egewgeg',
            academic_year__year=2024,
            education_group_type__name=TrainingType.BACHELOR.name,
        )

        EducationGroupYearFactory(
            acronym='ABCD',
            title='Test title search',
            academic_year__year=2023,
            education_group_type__name=TrainingType.BACHELOR.name,
        )

        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )

        cls.url = reverse('admission:autocomplete:general-education-trainings')

    def test_general_education_without_query_and_year(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            {
                'pagination': {'more': False},
                'results': [
                    {'id': 'ABCD', 'text': 'ABCD - Test title search', 'type': TrainingType.BACHELOR.name},
                    {'id': 'FOOBAR', 'text': 'FOOBAR - wegweij wegioj egewgeg', 'type': TrainingType.BACHELOR.name},
                ],
            },
        )

    def test_general_education_with_acronym_query_but_no_year(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            {
                'q': 'foo',
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            {
                'pagination': {'more': False},
                'results': [
                    {'id': 'FOOBAR', 'text': 'FOOBAR - wegweij wegioj egewgeg', 'type': TrainingType.BACHELOR.name},
                ],
            },
        )

    def test_general_education_with_title_query_but_no_year(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            {
                'q': 'test',
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            {
                'pagination': {'more': False},
                'results': [
                    {'id': 'ABCD', 'text': 'ABCD - Test title search', 'type': TrainingType.BACHELOR.name},
                ],
            },
        )

    def test_general_education_with_year_but_no_query(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            {
                'forward': json.dumps({'annee_academique': '2024'}),
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            {
                'pagination': {'more': False},
                'results': [
                    {'id': 'FOOBAR', 'text': 'FOOBAR - wegweij wegioj egewgeg', 'type': TrainingType.BACHELOR.name},
                ],
            },
        )

    def test_general_education_with_year_and_query(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            {
                'forward': json.dumps({'annee_academique': '2024', 'type': TrainingType.BACHELOR.name}),
                'q': 'bar',
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            {
                'pagination': {'more': False},
                'results': [
                    {'id': 'FOOBAR', 'text': 'FOOBAR - wegweij wegioj egewgeg', 'type': TrainingType.BACHELOR.name},
                ],
            },
        )

        response = self.client.get(
            self.url,
            {
                'forward': json.dumps({'annee_academique': '2024'}),
                'q': 'test',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            {
                'pagination': {'more': False},
                'results': [],
            },
        )
