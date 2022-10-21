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
from admission.ddd.admission.formation_continue import commands as continuing_education_commands
from admission.ddd.admission.formation_generale import commands as general_education_commands
from admission.ddd.admission.doctorat.preparation import commands as doctorate_education_commands

from base.utils.serializers import DTOSerializer


class InitierPropositionGeneraleCommandSerializer(DTOSerializer):
    class Meta:
        source = general_education_commands.InitierPropositionCommand


class InitierPropositionContinueCommandSerializer(DTOSerializer):
    class Meta:
        source = continuing_education_commands.InitierPropositionCommand


class ModifierChoixFormationContinueCommandSerializer(DTOSerializer):
    class Meta:
        source = continuing_education_commands.ModifierChoixFormationCommand


class ModifierChoixFormationGeneraleCommandSerializer(DTOSerializer):
    class Meta:
        source = general_education_commands.ModifierChoixFormationCommand


class ModifierTypeAdmissionDoctoraleCommandSerializer(DTOSerializer):
    class Meta:
        source = doctorate_education_commands.ModifierTypeAdmissionCommand
