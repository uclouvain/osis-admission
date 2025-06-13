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
from django.db.models import Value
from django.db.models.functions import Concat

from admission.auth.roles.program_manager import ProgramManager


def get_admission_program_managers_names(education_group_id):
    """
    Return the concatenation of the names of the admission program managers of the specified education group.
    :param education_group_id: The id of the education group
    :return: a string containing the names of the managers
    """
    return ', '.join(
        ProgramManager.objects.filter(education_group_id=education_group_id)
        .annotate(person_name=Concat('person__first_name', Value(' '), 'person__last_name'))
        .values_list('person_name', flat=True)
    )
