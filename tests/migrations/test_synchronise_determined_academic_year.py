# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase

from admission.migrations.utils.synchronise_determined_academic_year import (
    update_determined_academic_year_for_submitted_admissions,
)
from admission.models.base import BaseAdmission
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.tests.factories.academic_year import AcademicYearFactory


class SynchroniseDeterminedAcademicYearTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.academic_years = {
            academic_year.year: academic_year
            for academic_year in AcademicYearFactory.produce(
                base_year=2023,
                number_past=3,
                number_future=3,
            )
        }

    def test_update_for_submitted_admission(self):
        submitted_admission_with_different_years = GeneralEducationAdmissionFactory(
            admitted=True,
            training__academic_year=self.academic_years[2024],
            determined_academic_year=self.academic_years[2025],
        )
        submitted_admission_with_same_year = GeneralEducationAdmissionFactory(
            admitted=True,
            training__academic_year=self.academic_years[2021],
            determined_academic_year=self.academic_years[2021],
        )
        not_submitted_admission_with_same_year = GeneralEducationAdmissionFactory(
            training__academic_year=self.academic_years[2022],
            determined_academic_year=self.academic_years[2022],
        )
        not_submitted_admission_with_different_year = GeneralEducationAdmissionFactory(
            training__academic_year=self.academic_years[2021],
            determined_academic_year=self.academic_years[2022],
        )

        update_determined_academic_year_for_submitted_admissions(base_admission_model=BaseAdmission)

        submitted_admission_with_different_years.refresh_from_db()
        submitted_admission_with_same_year.refresh_from_db()
        not_submitted_admission_with_same_year.refresh_from_db()
        not_submitted_admission_with_different_year.refresh_from_db()

        self.assertEqual(submitted_admission_with_different_years.determined_academic_year, self.academic_years[2024])
        self.assertEqual(submitted_admission_with_same_year.determined_academic_year, self.academic_years[2021])
        self.assertEqual(not_submitted_admission_with_same_year.determined_academic_year, self.academic_years[2022])
        self.assertEqual(
            not_submitted_admission_with_different_year.determined_academic_year, self.academic_years[2022]
        )
