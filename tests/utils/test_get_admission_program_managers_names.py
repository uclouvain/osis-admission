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

from admission.admission_utils.admission_program_managers_names import get_admission_program_managers_names
from admission.tests.factories.roles import ProgramManagerRoleFactory
from base.tests.factories.education_group import EducationGroupFactory


class GetAdmissionProgramManagersNamesTestCase(TestCase):
    def test_with_no_program_manager(self):
        education_group = EducationGroupFactory()
        result = get_admission_program_managers_names(education_group_id=education_group.pk)
        self.assertEqual(result, '')

    def test_with_several_program_managers(self):
        program_manager_1 = ProgramManagerRoleFactory()
        program_manager_2 = ProgramManagerRoleFactory(education_group=program_manager_1.education_group)
        program_manager_3 = ProgramManagerRoleFactory(education_group=program_manager_1.education_group)
        other_program_manager = ProgramManagerRoleFactory()

        result = get_admission_program_managers_names(education_group_id=program_manager_1.education_group_id)
        self.assertEqual(
            result,
            f'{program_manager_1.person.first_name} {program_manager_1.person.last_name}, '
            f'{program_manager_2.person.first_name} {program_manager_2.person.last_name}, '
            f'{program_manager_3.person.first_name} {program_manager_3.person.last_name}'
        )
