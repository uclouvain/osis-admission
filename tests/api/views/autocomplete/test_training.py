# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
from typing import Optional
from unittest import mock

from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework.test import APITestCase

from admission.ddd.admission.domain.enums import TypeFormation
from admission.tests import TESTING_CACHE_SETTING
from base.models.campus import Campus
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import DOCTORAL_COMMISSION, SECTOR
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.models.education_group_version import EducationGroupVersion


@override_settings(CACHES=TESTING_CACHE_SETTING)
class TrainingDateMockTestCase(APITestCase):
    past_year: Optional[AcademicYearFactory]
    current_year: Optional[AcademicYearFactory]
    next_year: Optional[AcademicYearFactory]
    today_date: Optional[datetime.date]
    academic_calendar_type = None

    # Mock the current date (2020) and create related academic years
    @classmethod
    def setUpTestData(cls) -> None:
        [cls.past_year, cls.current_year, cls.next_year] = AcademicYearFactory.produce(
            base_year=2020,
            number_past=1,
            number_future=1,
        )

        AcademicCalendarFactory(
            reference=cls.academic_calendar_type,
            data_year=cls.past_year,
            start_date=datetime.date(2019, 10, 1),
            end_date=datetime.date(2020, 9, 30),
        )
        AcademicCalendarFactory(
            reference=cls.academic_calendar_type,
            data_year=cls.current_year,
            start_date=datetime.date(2020, 10, 1),
            end_date=datetime.date(2021, 9, 30),
        )
        AcademicCalendarFactory(
            reference=cls.academic_calendar_type,
            data_year=cls.next_year,
            start_date=datetime.date(2021, 10, 1),
            end_date=datetime.date(2022, 9, 30),
        )

        cls.today_date = datetime.date(2020, 11, 15)

    def setUp(self):
        patcher = mock.patch('admission.infrastructure.admission.domain.service.annee_inscription_formation.datetime')
        self.addCleanup(patcher.stop)
        self.mock_date = patcher.start()
        self.mock_date.date.today.return_value = self.today_date


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class DoctorateAutocompleteTestCase(TrainingDateMockTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_calendar_type = AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT.name
        cls.first_campus = Campus.objects.get(external_id=CampusFactory().external_id)
        cls.second_campus = Campus.objects.get(external_id=CampusFactory().external_id)

        super().setUpTestData()
        cls.user = UserFactory()
        cls.root = EntityVersionFactory(
            entity_type='',
            acronym='UCL',
            parent=None,
        ).entity
        cls.sector = EntityVersionFactory(
            entity_type=SECTOR,
            acronym='SST',
            parent=cls.root,
        ).entity
        cls.management_entity = EntityVersionFactory(
            entity_type=DOCTORAL_COMMISSION,
            acronym='CDSC',
            parent=cls.sector,
        ).entity

        cls.last_year_doctorate = EducationGroupYearFactory(
            academic_year=cls.past_year,
            education_group_type__name=TrainingType.PHD.name,
            management_entity=cls.management_entity,
        )
        group_year = GroupYearFactory(main_teaching_campus=cls.first_campus)
        EducationGroupVersion.objects.create(root_group_id=group_year.pk, offer=cls.last_year_doctorate)

        cls.current_year_first_doctorate = EducationGroupYearFactory(
            academic_year=cls.current_year,
            education_group_type__name=TrainingType.PHD.name,
            management_entity=cls.management_entity,
        )
        group_year = GroupYearFactory(main_teaching_campus=cls.second_campus)
        EducationGroupVersion.objects.create(root_group_id=group_year.pk, offer=cls.current_year_first_doctorate)

        cls.current_year_second_doctorate = EducationGroupYearFactory(
            academic_year=cls.current_year,
            education_group_type__name=TrainingType.PHD.name,
            management_entity=cls.management_entity,
        )
        group_year = GroupYearFactory(main_teaching_campus=cls.first_campus)
        EducationGroupVersion.objects.create(root_group_id=group_year.pk, offer=cls.current_year_second_doctorate)

        cls.next_year_doctorate = EducationGroupYearFactory(
            academic_year=cls.next_year,
            education_group_type__name=TrainingType.PHD.name,
            management_entity=cls.management_entity,
        )
        group_year = GroupYearFactory(main_teaching_campus=cls.first_campus)
        EducationGroupVersion.objects.create(root_group_id=group_year.pk, offer=cls.next_year_doctorate)

    def test_autocomplete_sectors(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-sector'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 1)

    def test_autocomplete_sectors_with_year_outside_calendar_range(self):
        self.mock_date.date.today.return_value = datetime.date(2015, 10, 1)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-sector'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 0)

    def test_autocomplete_doctorate(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-doctorate', sigle='SST'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 2)
        self.assertCountEqual(
            [doctorate['sigle'] for doctorate in response.json()],
            [self.current_year_first_doctorate.acronym, self.current_year_second_doctorate.acronym],
        )

    def test_autocomplete_doctorate_with_campus(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-doctorate', sigle='SST'),
            format='json',
            data={'campus': str(self.second_campus.uuid)},
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['sigle'], self.current_year_first_doctorate.acronym)

    def test_autocomplete_doctorate_a_day_before_calendar_start(self):
        self.mock_date.date.today.return_value = datetime.date(2020, 9, 30)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-doctorate', sigle='SST'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['sigle'], self.last_year_doctorate.acronym)

    def test_autocomplete_doctorate_the_day_of_the_calendar_start(self):
        self.mock_date.date.today.return_value = datetime.date(2020, 10, 1)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-doctorate', sigle='SST'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 2)
        self.assertCountEqual(
            [doctorate['sigle'] for doctorate in response.json()],
            [self.current_year_first_doctorate.acronym, self.current_year_second_doctorate.acronym],
        )

    def test_autocomplete_doctorate_the_day_of_the_calendar_end(self):
        self.mock_date.date.today.return_value = datetime.date(2021, 9, 30)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-doctorate', sigle='SST'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 2)
        self.assertCountEqual(
            [doctorate['sigle'] for doctorate in response.json()],
            [self.current_year_first_doctorate.acronym, self.current_year_second_doctorate.acronym],
        )

    def test_autocomplete_doctorate_a_day_after_calendar_end(self):
        self.mock_date.date.today.return_value = datetime.date(2021, 10, 1)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-doctorate', sigle='SST'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['sigle'], self.next_year_doctorate.acronym)

    def test_autocomplete_doctorate_outside_calendar_range(self):
        self.mock_date.date.today.return_value = datetime.date(2015, 10, 1)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-doctorate', sigle='SST'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 0)


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class GeneralEducationAutocompleteTestCase(TrainingDateMockTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_calendar_type = AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name
        cls.first_campus = Campus.objects.get(external_id=CampusFactory().external_id)
        cls.second_campus = Campus.objects.get(external_id=CampusFactory().external_id)

        super().setUpTestData()
        cls.user = UserFactory()

        cls.last_year_training = EducationGroupYearFactory(
            academic_year=cls.past_year,
            education_group_type__name=TrainingType.CERTIFICATE.name,
            title='Certificat en informatique 1',
        )
        group_year = GroupYearFactory(main_teaching_campus=cls.first_campus)
        EducationGroupVersion.objects.create(root_group_id=group_year.pk, offer=cls.last_year_training)

        cls.current_year_computer_certificate = EducationGroupYearFactory(
            academic_year=cls.current_year,
            education_group_type__name=TrainingType.CERTIFICATE.name,
            title='Certificat en informatique 1',
        )
        group_year = GroupYearFactory(main_teaching_campus=cls.first_campus)
        EducationGroupVersion.objects.create(root_group_id=group_year.pk, offer=cls.current_year_computer_certificate)

        cls.current_year_biologist_certificate = EducationGroupYearFactory(
            academic_year=cls.current_year,
            education_group_type__name=TrainingType.CERTIFICATE.name,
            title='Certificat en biologie 1',
        )
        group_year = GroupYearFactory(main_teaching_campus=cls.first_campus)
        EducationGroupVersion.objects.create(root_group_id=group_year.pk, offer=cls.current_year_biologist_certificate)

        cls.current_year_computer_master = EducationGroupYearFactory(
            academic_year=cls.current_year,
            education_group_type__name=TrainingType.MASTER_MA_120.name,
            title='Master en informatique 1',
        )
        group_year = GroupYearFactory(main_teaching_campus=cls.second_campus)
        EducationGroupVersion.objects.create(root_group_id=group_year.pk, offer=cls.current_year_computer_master)

        cls.next_year_training = EducationGroupYearFactory(
            academic_year=cls.next_year,
            education_group_type__name=TrainingType.CERTIFICATE.name,
            title='Certificat en informatique 1',
        )
        group_year = GroupYearFactory(main_teaching_campus=cls.first_campus)
        EducationGroupVersion.objects.create(root_group_id=group_year.pk, offer=cls.next_year_training)

    def test_autocomplete_general_education_with_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-general-education'),
            format='json',
            data={'name': 'informatique 1'},
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 2)
        self.assertCountEqual(
            [training['sigle'] for training in response.json()],
            [self.current_year_computer_certificate.acronym, self.current_year_computer_master.acronym],
        )

    def test_autocomplete_general_education_with_campus(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-general-education'),
            format='json',
            data={'campus': str(self.first_campus.uuid)},
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 2)
        self.assertCountEqual(
            [training['sigle'] for training in response.json()],
            [self.current_year_computer_certificate.acronym, self.current_year_biologist_certificate.acronym],
        )

    def test_autocomplete_general_education_with_type(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-general-education'),
            format='json',
            data={'type': TypeFormation.CERTIFICAT.name},
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 2)
        self.assertCountEqual(
            [training['sigle'] for training in response.json()],
            [self.current_year_computer_certificate.acronym, self.current_year_biologist_certificate.acronym],
        )

    def test_autocomplete_general_education_a_day_before_calendar_start(self):
        self.mock_date.date.today.return_value = datetime.date(2020, 9, 30)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-general-education'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['sigle'], self.last_year_training.acronym)

    def test_autocomplete_general_education_the_day_of_the_calendar_start(self):
        self.mock_date.date.today.return_value = datetime.date(2020, 10, 1)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-general-education'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 3)
        self.assertCountEqual(
            [doctorate['sigle'] for doctorate in response.json()],
            [
                self.current_year_computer_certificate.acronym,
                self.current_year_biologist_certificate.acronym,
                self.current_year_computer_master.acronym,
            ],
        )

    def test_autocomplete_general_education_the_day_of_the_calendar_end(self):
        self.mock_date.date.today.return_value = datetime.date(2021, 9, 30)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-general-education'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 3)
        self.assertCountEqual(
            [doctorate['sigle'] for doctorate in response.json()],
            [
                self.current_year_computer_certificate.acronym,
                self.current_year_biologist_certificate.acronym,
                self.current_year_computer_master.acronym,
            ],
        )

    def test_autocomplete_general_education_a_day_after_calendar_end(self):
        self.mock_date.date.today.return_value = datetime.date(2021, 10, 1)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-general-education'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['sigle'], self.next_year_training.acronym)

    def test_autocomplete_general_education_outside_calendar_range(self):
        self.mock_date.date.today.return_value = datetime.date(2015, 10, 1)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-general-education'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 0)


@override_settings(ROOT_URLCONF='admission.api.url_v1')
class ContinuingEducationAutocompleteTestCase(TrainingDateMockTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_calendar_type = AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT.name

        super().setUpTestData()

        cls.user = UserFactory()
        cls.first_campus = Campus.objects.get(external_id=CampusFactory().external_id)
        cls.second_campus = Campus.objects.get(external_id=CampusFactory().external_id)

        cls.last_year_training = EducationGroupYearFactory(
            academic_year=cls.past_year,
            education_group_type__name=TrainingType.CERTIFICATE_OF_SUCCESS.name,
            title='Certificat de succès en informatique 1',
        )
        group_year = GroupYearFactory(main_teaching_campus=cls.first_campus)
        EducationGroupVersion.objects.create(root_group_id=group_year.pk, offer=cls.last_year_training)

        cls.current_year_computer_certificate_of_success = EducationGroupYearFactory(
            academic_year=cls.current_year,
            education_group_type__name=TrainingType.CERTIFICATE_OF_SUCCESS.name,
            title='Certificat de succès en informatique 1',
        )
        group_year = GroupYearFactory(main_teaching_campus=cls.second_campus)
        EducationGroupVersion.objects.create(
            root_group_id=group_year.pk,
            offer=cls.current_year_computer_certificate_of_success,
        )

        cls.current_year_biologist_certificate_of_success = EducationGroupYearFactory(
            academic_year=cls.current_year,
            education_group_type__name=TrainingType.CERTIFICATE_OF_SUCCESS.name,
            title='Certificat de succès en biologie 1',
            enrollment_campus=cls.current_year_computer_certificate_of_success.enrollment_campus,
        )
        group_year = GroupYearFactory(main_teaching_campus=cls.second_campus)
        EducationGroupVersion.objects.create(
            root_group_id=group_year.pk,
            offer=cls.current_year_biologist_certificate_of_success,
        )

        cls.current_year_computer_certificate_of_participation = EducationGroupYearFactory(
            academic_year=cls.current_year,
            education_group_type__name=TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
            title='Certificat de participation en informatique 1',
        )
        group_year = GroupYearFactory(main_teaching_campus=cls.first_campus)
        EducationGroupVersion.objects.create(
            root_group_id=group_year.pk,
            offer=cls.current_year_computer_certificate_of_participation,
        )

        cls.next_year_training = EducationGroupYearFactory(
            academic_year=cls.next_year,
            education_group_type__name=TrainingType.CERTIFICATE_OF_SUCCESS.name,
            title='Certificat de succès en informatique 1',
        )
        group_year = GroupYearFactory(main_teaching_campus=cls.second_campus)
        EducationGroupVersion.objects.create(
            root_group_id=group_year.pk,
            offer=cls.next_year_training,
        )

    def test_autocomplete_continuing_education_with_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-continuing-education'),
            format='json',
            data={'name': 'informatique 1'},
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 2)
        self.assertCountEqual(
            [training['sigle'] for training in response.json()],
            [
                self.current_year_computer_certificate_of_success.acronym,
                self.current_year_computer_certificate_of_participation.acronym,
            ],
        )

    def test_autocomplete_continuing_education_with_campus(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-continuing-education'),
            format='json',
            data={'campus': str(self.second_campus.uuid)},
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 2)
        self.assertCountEqual(
            [training['sigle'] for training in response.json()],
            [
                self.current_year_computer_certificate_of_success.acronym,
                self.current_year_biologist_certificate_of_success.acronym,
            ],
        )

    def test_autocomplete_continuing_education_a_day_before_calendar_start(self):
        self.mock_date.date.today.return_value = datetime.date(2020, 9, 30)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-continuing-education'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['sigle'], self.last_year_training.acronym)

    def test_autocomplete_continuing_education_the_day_of_the_calendar_start(self):
        self.mock_date.date.today.return_value = datetime.date(2020, 10, 1)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-continuing-education'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 3)
        self.assertCountEqual(
            [doctorate['sigle'] for doctorate in response.json()],
            [
                self.current_year_computer_certificate_of_success.acronym,
                self.current_year_biologist_certificate_of_success.acronym,
                self.current_year_computer_certificate_of_participation.acronym,
            ],
        )

    def test_autocomplete_continuing_education_the_day_of_the_calendar_end(self):
        self.mock_date.date.today.return_value = datetime.date(2021, 9, 30)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-continuing-education'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 3)
        self.assertCountEqual(
            [doctorate['sigle'] for doctorate in response.json()],
            [
                self.current_year_computer_certificate_of_success.acronym,
                self.current_year_biologist_certificate_of_success.acronym,
                self.current_year_computer_certificate_of_participation.acronym,
            ],
        )

    def test_autocomplete_continuing_education_a_day_after_calendar_end(self):
        self.mock_date.date.today.return_value = datetime.date(2021, 10, 1)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-continuing-education'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['sigle'], self.next_year_training.acronym)

    def test_autocomplete_continuing_education_outside_calendar_range(self):
        self.mock_date.date.today.return_value = datetime.date(2015, 10, 1)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            resolve_url('autocomplete-continuing-education'),
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()), 0)
