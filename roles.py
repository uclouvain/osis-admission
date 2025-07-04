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
from admission.auth.predicates.common import is_part_of_education_group
from admission.auth.predicates.doctorate import (
    is_enrolled,
    is_pre_admission,
)
from admission.auth.roles.admission_reader import AdmissionReader
from admission.auth.roles.ca_member import CommitteeMember
from admission.auth.roles.candidate import Candidate
from admission.auth.roles.central_manager import CentralManager
from admission.auth.roles.doctorate_committee_member import DoctorateCommitteeMember
from admission.auth.roles.program_manager import ProgramManager
from admission.auth.roles.promoter import Promoter
from admission.auth.roles.sceb import Sceb
from admission.auth.roles.sic_management import SicManagement
from osis_role import role

role.role_manager.register(Candidate)
role.role_manager.register(CommitteeMember)
role.role_manager.register(DoctorateCommitteeMember)
role.role_manager.register(Promoter)
role.role_manager.register(Sceb)
role.role_manager.register(ProgramManager)
role.role_manager.register(CentralManager)
role.role_manager.register(AdmissionReader)
role.role_manager.register(SicManagement)
