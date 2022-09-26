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
import datetime
from datetime import timedelta
from unittest import mock

from django.db.models import QuerySet
from django.test import TestCase

from admission.calendar.admission_calendar import (
    DoctorateAdmissionCalendar,
    ContinuingEducationAdmissionCalendar,
    GeneralEducationAdmissionCalendar,
)
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.models.academic_calendar import AcademicCalendar
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory


class TestAdmissionCalendarGeneration(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.today_date = datetime.date(2020, 12, 1)
        cls.today_datetime = datetime.datetime(2020, 12, 1)

        for year in range(2019, 2026):
            AcademicYearFactory(year=year)

    def setUp(self) -> None:
        # Mock datetime to return the 2020 year as the current year
        patcher = mock.patch('base.models.academic_year.timezone')
        self.addCleanup(patcher.stop)
        self.mock_date = patcher.start()
        self.mock_date.now.return_value = self.today_datetime

    def test_creation_academic_calendar_for_doctorate(self):
        has_calendar_events = AcademicCalendar.objects.filter(
            reference=AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT.name,
        ).exists()

        self.assertFalse(has_calendar_events)

        DoctorateAdmissionCalendar.ensure_consistency_until_n_plus_6()

        calendar_events: QuerySet[AcademicCalendar] = (
            AcademicCalendar.objects.filter(
                reference=AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT.name,
            )
            .select_related('data_year')
            .order_by('data_year__year')
        )

        self.assertEqual(len(calendar_events), 7)

        self.assertEqual(calendar_events[0].data_year.year, 2019)
        self.assertEqual(calendar_events[0].start_date, datetime.date(2019, 7, 1))
        self.assertEqual(calendar_events[0].end_date, datetime.date(2020, 6, 30))

    def test_creation_academic_calendar_for_continuing_education(self):
        has_calendar_events = AcademicCalendar.objects.filter(
            reference=AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT.name,
        ).exists()

        self.assertFalse(has_calendar_events)

        ContinuingEducationAdmissionCalendar.ensure_consistency_until_n_plus_6()

        calendar_events: QuerySet[AcademicCalendar] = (
            AcademicCalendar.objects.filter(
                reference=AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT.name,
            )
            .select_related('data_year')
            .order_by('data_year__year')
        )

        self.assertEqual(len(calendar_events), 7)

        self.assertEqual(calendar_events[0].data_year.year, 2019)
        self.assertEqual(calendar_events[0].start_date, datetime.date(2019, 7, 1))
        self.assertEqual(calendar_events[0].end_date, datetime.date(2020, 6, 30))

    def test_creation_academic_calendar_for_general_education(self):
        has_calendar_events = AcademicCalendar.objects.filter(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
        ).exists()

        self.assertFalse(has_calendar_events)

        GeneralEducationAdmissionCalendar.ensure_consistency_until_n_plus_6()

        calendar_events: QuerySet[AcademicCalendar] = (
            AcademicCalendar.objects.filter(
                reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            )
            .select_related('data_year')
            .order_by('data_year__year')
        )

        self.assertEqual(len(calendar_events), 7)

        self.assertEqual(calendar_events[0].data_year.year, 2019)
        self.assertEqual(calendar_events[0].start_date, datetime.date(2018, 11, 1))
        self.assertEqual(calendar_events[0].end_date, datetime.date(2019, 10, 31))


class TestAllowedRegistrationYear(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.academic_year = AcademicYearFactory(year=2020)
        cls.today_date = datetime.date(2020, 10, 10)

    def setUp(self) -> None:
        # Mock datetime
        patcher = mock.patch(
            'admission.infrastructure.admission.domain.service.annee_inscription_formation.datetime'
        )
        self.addCleanup(patcher.stop)
        self.mock_date = patcher.start()
        self.mock_date.date.today.return_value = self.today_date

    def test_when_no_event(self):
        has_calendar_events = AcademicCalendar.objects.filter(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
        ).exists()

        year = AnneeInscriptionFormationTranslator.recuperer(AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT)

        self.assertFalse(has_calendar_events)
        self.assertIsNone(year)

    def test_when_event_starts_a_day_before(self):
        AcademicCalendarFactory(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date=self.today_date - timedelta(days=1),
            end_date=self.today_date + timedelta(days=1),
            data_year=self.academic_year,
        )
        year = AnneeInscriptionFormationTranslator.recuperer(AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT)
        self.assertEqual(year, self.academic_year.year)

    def test_when_event_starts_same_day(self):
        AcademicCalendarFactory(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date=self.today_date,
            end_date=self.today_date + timedelta(days=1),
            data_year=self.academic_year,
        )
        year = AnneeInscriptionFormationTranslator.recuperer(AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT)
        self.assertEqual(year, self.academic_year.year)

    def test_when_event_starts_a_day_after(self):
        AcademicCalendarFactory(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date=self.today_date + timedelta(days=1),
            end_date=self.today_date + timedelta(days=2),
            data_year=self.academic_year,
        )
        year = AnneeInscriptionFormationTranslator.recuperer(AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT)
        self.assertIsNone(year)

    def test_when_event_ends_same_day(self):
        AcademicCalendarFactory(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date=self.today_date - timedelta(days=1),
            end_date=self.today_date,
            data_year=self.academic_year,
        )
        year = AnneeInscriptionFormationTranslator.recuperer(AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT)
        self.assertEqual(year, self.academic_year.year)

    def test_when_event_ends_a_day_before(self):
        AcademicCalendarFactory(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date=self.today_date - timedelta(days=2),
            end_date=self.today_date - timedelta(days=1),
            data_year=self.academic_year,
        )
        year = AnneeInscriptionFormationTranslator.recuperer(AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT)
        self.assertIsNone(year)
