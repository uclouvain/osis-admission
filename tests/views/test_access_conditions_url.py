# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

import datetime
import freezegun
from django.test import TestCase, override_settings
from django.urls import reverse

from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationTrainingFactory
from admission.tests.factories.general_education import GeneralEducationTrainingFactory
from admission.tests.factories.roles import SicManagementRoleFactory
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests import QueriesAssertionsMixin
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory


@freezegun.freeze_time('2023-01-01')
@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class AdmissionAccessConditionsURLTestCase(QueriesAssertionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sic_management_user = SicManagementRoleFactory().person.user

        cls.academic_years = AcademicYearFactory.produce(2023, number_past=2, number_future=2)

        cls.access_condition_url_academic_calendars = [
            AcademicCalendarFactory(
                data_year=academic_year,
                reference=AcademicCalendarTypes.ADMISSION_ACCESS_CONDITIONS_URL.name,
                start_date=academic_year.start_date - datetime.timedelta(days=365),
                end_date=academic_year.end_date - datetime.timedelta(days=365),
            )
            for academic_year in cls.academic_years
        ]

        cls.continuing_academic_calendars = [
            AcademicCalendarFactory(
                data_year=academic_year,
                reference=AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT.name,
            )
            for academic_year in cls.academic_years
        ]

        # Targeted url
        cls.conditions_url = 'admission:access-conditions-url'

    def test_access_conditions_url_with_a_doctorate(self):
        self.client.force_login(user=self.sic_management_user)

        doctorate_admission = DoctorateAdmissionFactory()

        response = self.client.get(
            reverse(
                self.conditions_url,
                kwargs={
                    'training_type': doctorate_admission.training.education_group_type.name,
                    'training_acronym': doctorate_admission.training.acronym,
                    'partial_training_acronym': doctorate_admission.training.partial_acronym,
                },
            )
        )

        self.assertRedirects(
            response=response,
            expected_url='https://uclouvain.be/fr/etudier/inscriptions/conditions-doctorats.html',
            status_code=302,
            fetch_redirect_response=False,
        )

    def test_access_conditions_url_with_a_general_training(self):
        self.client.force_login(user=self.sic_management_user)

        training = GeneralEducationTrainingFactory()

        response = self.client.get(
            reverse(
                self.conditions_url,
                kwargs={
                    'training_type': training.education_group_type.name,
                    'training_acronym': training.acronym,
                    'partial_training_acronym': training.partial_acronym,
                },
            ),
        )

        self.assertRedirects(
            response=response,
            expected_url=f'https://uclouvain.be/prog-2023-{training.acronym}-cond_adm',
            status_code=302,
            fetch_redirect_response=False,
        )

    def test_access_conditions_url_with_a_continuing_training(self):
        self.client.force_login(user=self.sic_management_user)

        training = ContinuingEducationTrainingFactory()

        response = self.client.get(
            reverse(
                self.conditions_url,
                kwargs={
                    'training_type': training.education_group_type.name,
                    'training_acronym': training.acronym,
                    'partial_training_acronym': training.partial_acronym,
                },
            ),
        )

        self.assertRedirects(
            response=response,
            expected_url=f'https://uclouvain.be/prog-2022-{training.acronym}-cond_adm',
            status_code=302,
            fetch_redirect_response=False,
        )
