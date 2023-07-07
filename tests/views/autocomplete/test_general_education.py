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
from django.conf import settings
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from admission.ddd.admission.formation_generale.commands import RechercherFormationsGereesQuery
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.general_education import GeneralEducationTrainingFactory
from admission.tests.factories.roles import ProgramManagerRoleFactory
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.user import UserFactory
from infrastructure.messages_bus import message_bus_instance
from program_management.models.education_group_version import EducationGroupVersion


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
                    {'id': 'ABCD', 'text': 'ABCD - Test title search'},
                    {'id': 'FOOBAR', 'text': 'FOOBAR - wegweij wegioj egewgeg'},
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
                    {'id': 'FOOBAR', 'text': 'FOOBAR - wegweij wegioj egewgeg'},
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
                    {'id': 'ABCD', 'text': 'ABCD - Test title search'},
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
                    {'id': 'FOOBAR', 'text': 'FOOBAR - wegweij wegioj egewgeg'},
                ],
            },
        )

    def test_general_education_with_year_and_query(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            self.url,
            {
                'forward': json.dumps({'annee_academique': '2024'}),
                'q': 'bar',
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            {
                'pagination': {'more': False},
                'results': [
                    {'id': 'FOOBAR', 'text': 'FOOBAR - wegweij wegioj egewgeg'},
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


class ManagedGeneralEducationTrainingsAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        entity = EntityWithVersionFactory()

        cls.first_year_computer_training = GeneralEducationTrainingFactory(
            academic_year____year=2021,
            management_entity=entity,
            academic_year=cls.academic_years[0],
            title='Informatique',
            title_english='Computer Science',
            acronym='CS1',
        )
        cls.first_year_computer_training_teaching_campus = (
            EducationGroupVersion.objects.filter(offer=cls.first_year_computer_training)
            .first()
            .root_group.main_teaching_campus.name
        )

        cls.first_year_biology_training = GeneralEducationTrainingFactory(
            academic_year____year=2021,
            management_entity=entity,
            academic_year=cls.academic_years[0],
            title='Biologie',
            title_english='Biology',
            acronym='BIO1',
        )

        cls.second_year_computer_training = GeneralEducationTrainingFactory(
            academic_year__year=2022,
            management_entity=entity,
            academic_year=cls.academic_years[1],
            title='Informatique',
            title_english='Computer Science',
            acronym='CS1',
        )

        cls.cdd_manager = ProgramManagerRoleFactory(
            education_group=cls.first_year_computer_training.education_group
        ).person

        for training in [cls.first_year_biology_training, cls.second_year_computer_training]:
            ProgramManagerRoleFactory(education_group=training.education_group, person=cls.cdd_manager)

        cls.url = reverse('admission:autocomplete:managed-general-education-trainings')

    def test_search_by_fr_title(self):
        self.client.force_login(self.cdd_manager.user)

        response = self.client.get(self.url, data={'forward': '{"annee_academique": "2021"}', 'q': 'Informatique'})

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']
        self.assertEqual(len(results), 1)

        self.assertEqual(
            results[0],
            {
                'id': str(self.first_year_computer_training.uuid),
                'text': f'{self.first_year_computer_training.acronym} - {self.first_year_computer_training.title} '
                f'({self.first_year_computer_training_teaching_campus})',
            },
        )
