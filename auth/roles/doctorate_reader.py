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

from django.utils.translation import gettext_lazy as _
from rules import RuleSet, always_allow

from admission.auth.predicates import doctorate
from osis_role.contrib.models import RoleModel


class DoctorateReader(RoleModel):
    class Meta:
        verbose_name = _("Role: Doctorate reader")
        verbose_name_plural = _("Role: Doctorate readers")
        group_name = "doctorate_reader"

    @classmethod
    def rule_set(cls):
        ruleset = {
            'admission.view_doctorateadmission': always_allow,
            'admission.view_admission_person': always_allow,
            'admission.view_admission_coordinates': always_allow,
            'admission.view_admission_secondary_studies': always_allow,
            'admission.view_admission_languages': always_allow,
            'admission.view_admission_curriculum': always_allow,
            'admission.view_admission_project': always_allow,
            'admission.view_admission_cotutelle': doctorate.is_admission,
            'admission.view_admission_supervision': always_allow,
            'admission.view_dossiers': always_allow,
            'admission.view_internalnote': always_allow,
        }
        return RuleSet(ruleset)
