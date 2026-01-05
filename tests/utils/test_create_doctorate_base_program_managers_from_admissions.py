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

from admission.admission_utils.copy_program_managers_from_admission_to_base import (
    copy_program_managers_from_admission_to_base,
)
from admission.auth.roles.program_manager import (
    ProgramManager as AdmissionProgramManager,
)
from admission.tests.factories.continuing_education import (
    ContinuingEducationTrainingFactory,
)
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.general_education import GeneralEducationTrainingFactory
from admission.tests.factories.roles import (
    ProgramManagerRoleFactory as AdmissionProgramManagerFactory,
)
from base.auth.roles.program_manager import ProgramManager
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.program_manager import ProgramManagerFactory


class CopyProgramManagersFromAdmissionToBaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.base_program_managers = ProgramManager.objects.all()
        cls.admission_program_managers = AdmissionProgramManager.objects.all()
        cls.base_program_managers.delete()
        cls.admission_program_managers.delete()

        cls.doctorate_trainings = {f'{i}': DoctorateFactory().education_group for i in range(3)}
        cls.general_training = GeneralEducationTrainingFactory().education_group
        cls.continuing_training = ContinuingEducationTrainingFactory().education_group

    def test_if_no_program_managers(self):
        copy_program_managers_from_admission_to_base(training_type=TrainingType.PHD)

        self.assertEqual(self.base_program_managers.count(), 0)

    def test_with_several_admission_program_managers(self):
        already_added_a_manager_1 = AdmissionProgramManagerFactory(education_group=self.doctorate_trainings['1'])
        already_added_b_manager_1 = ProgramManagerFactory(
            person=already_added_a_manager_1.person,
            education_group=self.doctorate_trainings['1'],
        )

        already_added_a_manager_2 = AdmissionProgramManagerFactory(education_group=self.doctorate_trainings['2'])
        already_added_b_manager_2 = ProgramManagerFactory(
            person=already_added_a_manager_2.person,
            education_group=self.doctorate_trainings['2'],
        )

        a_manager_to_add_1_t1 = AdmissionProgramManagerFactory(education_group=self.doctorate_trainings['1'])
        a_manager_to_add_1_t2 = AdmissionProgramManagerFactory(
            person=a_manager_to_add_1_t1.person,
            education_group=self.doctorate_trainings['2'],
        )
        a_manager_to_add_2 = AdmissionProgramManagerFactory(education_group=self.doctorate_trainings['2'])

        a_manager_to_ignore_1 = AdmissionProgramManagerFactory(education_group=self.general_training)
        a_manager_to_ignore_2 = AdmissionProgramManagerFactory(education_group=self.continuing_training)

        copy_program_managers_from_admission_to_base(training_type=TrainingType.PHD)

        self.assertEqual(self.base_program_managers.count(), 5)

        # The previous ones
        self.assertTrue(
            self.base_program_managers.filter(
                person=already_added_a_manager_1.person,
                education_group=already_added_a_manager_1.education_group,
            ).exists()
        )
        self.assertTrue(
            self.base_program_managers.filter(
                person=already_added_a_manager_2.person,
                education_group=already_added_a_manager_2.education_group,
            ).exists()
        )

        # The new ones
        self.assertTrue(
            self.base_program_managers.filter(
                person=a_manager_to_add_1_t1.person,
                education_group=a_manager_to_add_1_t1.education_group,
            ).exists()
        )
        self.assertTrue(
            self.base_program_managers.filter(
                person=a_manager_to_add_1_t2.person,
                education_group=a_manager_to_add_1_t2.education_group,
            ).exists()
        )
        self.assertTrue(
            self.base_program_managers.filter(
                person=a_manager_to_add_2.person,
                education_group=a_manager_to_add_2.education_group,
            ).exists()
        )
