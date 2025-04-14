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

from admission.migrations.utils.initialize_has_scholarship_fields import (
    initialize_has_scholarship_fields,
)
from admission.models import GeneralEducationAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.tests.factories.education_group_year import (
    EducationGroupYearBachelorFactory,
    Master120TrainingFactory,
)
from reference.tests.factories.scholarship import (
    DoubleDegreeScholarshipFactory,
    ErasmusMundusScholarshipFactory,
    InternationalScholarshipFactory,
)


class InitializeHasScholarshipFieldsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.double_degree_scholarship = DoubleDegreeScholarshipFactory()
        cls.erasmus_mundus_scholarship = ErasmusMundusScholarshipFactory()
        cls.international_scolarship = InternationalScholarshipFactory()
        cls.master_training = Master120TrainingFactory()
        cls.bachelor_training = EducationGroupYearBachelorFactory()
        cls.doctorate_admission = DoctorateAdmissionFactory()
        cls.continuing_education_admission = ContinuingEducationAdmissionFactory()

    def test_initialization(self):
        master_admission_with_double_degree_scholarship: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.master_training,
            erasmus_mundus_scholarship=None,
            international_scholarship=None,
            double_degree_scholarship=self.double_degree_scholarship,
        )

        master_admission_with_erasmus_mundus_scholarship: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.master_training,
            double_degree_scholarship=None,
            international_scholarship=None,
            erasmus_mundus_scholarship=self.erasmus_mundus_scholarship,
        )

        master_admission_with_international_scholarship: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.master_training,
            erasmus_mundus_scholarship=None,
            double_degree_scholarship=None,
            international_scholarship=self.international_scolarship,
        )

        bachelor_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.bachelor_training,
        )

        updated_admissions = initialize_has_scholarship_fields(
            admission_class=GeneralEducationAdmission,
            on_migration=False,
        )

        self.assertEqual(len(updated_admissions), 3)

        master_admission_with_double_degree_scholarship.refresh_from_db()

        self.assertTrue(master_admission_with_double_degree_scholarship.has_double_degree_scholarship)
        self.assertFalse(master_admission_with_double_degree_scholarship.has_international_scholarship)
        self.assertFalse(master_admission_with_double_degree_scholarship.has_erasmus_mundus_scholarship)

        master_admission_with_erasmus_mundus_scholarship.refresh_from_db()

        self.assertFalse(master_admission_with_erasmus_mundus_scholarship.has_double_degree_scholarship)
        self.assertFalse(master_admission_with_erasmus_mundus_scholarship.has_international_scholarship)
        self.assertTrue(master_admission_with_erasmus_mundus_scholarship.has_erasmus_mundus_scholarship)

        master_admission_with_international_scholarship.refresh_from_db()

        self.assertFalse(master_admission_with_international_scholarship.has_double_degree_scholarship)
        self.assertTrue(master_admission_with_international_scholarship.has_international_scholarship)
        self.assertFalse(master_admission_with_international_scholarship.has_erasmus_mundus_scholarship)

        bachelor_admission.refresh_from_db()

        self.assertIsNone(bachelor_admission.has_double_degree_scholarship)
        self.assertIsNone(bachelor_admission.has_international_scholarship)
        self.assertIsNone(bachelor_admission.has_erasmus_mundus_scholarship)
