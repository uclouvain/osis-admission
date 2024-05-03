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

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from admission.tests.factories.continuing_education import ContinuingEducationTrainingFactory
from admission.tests.factories.general_education import GeneralEducationTrainingFactory
from admission.tests.factories.roles import ProgramManagerRoleFactory, CentralManagerRoleFactory
from base.models.enums.state_iufc import StateIUFC
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.user import UserFactory
from education_group.auth.scope import Scope
from program_management.models.education_group_version import EducationGroupVersion


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

        cls.url = reverse('admission:autocomplete:managed-education-trainings')

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

    def test_search_with_excluded_training(self):
        self.client.force_login(self.cdd_manager.user)

        response = self.client.get(
            self.url,
            data={
                'forward': json.dumps(
                    {
                        'annee_academique': '2021',
                    }
                ),
            },
        )

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']
        self.assertEqual(len(results), 2)

        self.assertCountEqual(
            [result['id'] for result in results],
            [str(self.first_year_computer_training.uuid), str(self.first_year_biology_training.uuid)],
        )

        response = self.client.get(
            self.url,
            data={
                'forward': json.dumps(
                    {
                        'excluded_training': str(self.first_year_computer_training.uuid),
                        'annee_academique': '2021',
                    }
                ),
            },
        )

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']
        self.assertEqual(len(results), 1)

        self.assertEqual(
            results[0]['id'],
            str(self.first_year_biology_training.uuid),
        )


class ContinuingManagedEducationTrainingsAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        entity = EntityWithVersionFactory()
        other_entity = EntityWithVersionFactory()

        cls.first_year_computer_training = ContinuingEducationTrainingFactory(
            management_entity=entity,
            academic_year=academic_years[0],
            title='Informatique',
            title_english='Computer Science',
            acronym='CS1',
        )

        cls.first_year_biology_training = ContinuingEducationTrainingFactory(
            management_entity=entity,
            academic_year=academic_years[0],
            title='Biologie',
            title_english='Biology',
            acronym='BIO1',
        )

        cls.first_year_economics_training = ContinuingEducationTrainingFactory(
            academic_year=academic_years[0],
            title='Economie',
            title_english='',
            acronym='ECO1',
            management_entity=other_entity,
        )

        cls.second_year_computer_training = ContinuingEducationTrainingFactory(
            management_entity=entity,
            academic_year=academic_years[1],
            title='Informatique',
            title_english='Computer Science',
            acronym='CS1',
        )

        cls.cdd_manager = ProgramManagerRoleFactory(
            education_group=cls.first_year_computer_training.education_group
        ).person

        for training in [cls.first_year_economics_training, cls.second_year_computer_training]:
            ProgramManagerRoleFactory(education_group=training.education_group, person=cls.cdd_manager)

        cls.central_manager = CentralManagerRoleFactory(scopes=[Scope.IUFC.name], entity=entity).person

        cls.url = reverse('admission:autocomplete:continuing-managed-education-trainings')

    def test_filter_by_program_manager_role(self):
        self.client.force_login(self.cdd_manager.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertCountEqual(
            [result['id'] for result in results],
            [self.first_year_computer_training.acronym, self.first_year_economics_training.acronym],
        )

    def test_filter_by_central_manager_role(self):
        self.client.force_login(self.central_manager.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertCountEqual(
            [result['id'] for result in results],
            [self.first_year_computer_training.acronym, self.first_year_biology_training.acronym],
        )

    def test_filter_by_fr_title(self):
        self.client.force_login(self.central_manager.user)

        response = self.client.get(self.url, data={'q': 'Biologie'})

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        training = self.first_year_biology_training
        self.assertEqual(
            results,
            [
                {
                    'id': training.acronym,
                    'selected_text': f'{training.acronym} - {training.title}',
                    'text': f'{training.acronym} - {training.title}',
                    'state': StateIUFC.OPEN.name,
                    'registration_required': True,
                }
            ],
        )

    def test_filter_by_acronym(self):
        self.client.force_login(self.central_manager.user)

        response = self.client.get(self.url, data={'q': 'BIO1'})

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.first_year_biology_training.acronym)

    @override_settings(LANGUAGE_CODE=settings.LANGUAGE_CODE_EN)
    def test_filter_by_en_title(self):
        self.client.force_login(UserFactory())

        response = self.client.get(self.url, data={'q': 'Biology'})

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        training = self.first_year_biology_training
        self.assertEqual(
            results,
            [
                {
                    'id': training.acronym,
                    'selected_text': f'{training.acronym} - {training.title_english}',
                    'text': f'{training.acronym} - {training.title_english}',
                    'state': StateIUFC.OPEN.name,
                    'registration_required': True,
                }
            ],
        )

    @override_settings(LANGUAGE_CODE=settings.LANGUAGE_CODE_EN)
    def test_display_french_title_is_the_english_title_is_empty(self):
        self.client.force_login(UserFactory())

        response = self.client.get(self.url, data={'q': 'Econom'})

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        training = self.first_year_economics_training

        self.assertEqual(
            results,
            [
                {
                    'id': training.acronym,
                    'selected_text': f'{training.acronym} - {training.title}',
                    'text': f'{training.acronym} - {training.title}',
                    'state': StateIUFC.OPEN.name,
                    'registration_required': True,
                }
            ],
        )
