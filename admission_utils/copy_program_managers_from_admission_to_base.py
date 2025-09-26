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

from admission.auth.roles.program_manager import (
    ProgramManager as AdmissionProgramManager,
)
from base.auth.roles.program_manager import ProgramManager
from base.models.enums.education_group_types import TrainingType


def copy_program_managers_from_admission_to_base(training_type: TrainingType):
    """
    Add the program managers roles of the base app based on the ones specified in the admission app.

    :param training_type: The training type linked to the program manager role.
    """
    admission_program_managers = AdmissionProgramManager.objects.filter(
        education_group__educationgroupyear__education_group_type__name=training_type.name
    ).distinct()

    already_existing_base_program_managers = ProgramManager.objects.filter(
        education_group__educationgroupyear__education_group_type__name=training_type.name
    ).values_list('person_id', 'education_group_id')

    already_existing_base_program_managers_set = set(already_existing_base_program_managers)

    base_program_managers = [
        ProgramManager(
            person=manager.person,
            education_group=manager.education_group,
        )
        for manager in admission_program_managers
        if (manager.person_id, manager.education_group_id) not in already_existing_base_program_managers_set
    ]

    return ProgramManager.objects.bulk_create(base_program_managers)
