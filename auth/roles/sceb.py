# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

import rules
from django.utils.translation import gettext_lazy as _
from rules import RuleSet

from osis_role.contrib.models import RoleModel


class Sceb(RoleModel):
    """
    Gestionnaire SCEB

    Intervient dans la soutenance pour vérifier la pertinence de la publication de la thèse.
    """

    class Meta:
        verbose_name = _("Role: SCEB")
        verbose_name_plural = _("Role: SCEBs")
        group_name = "sceb"

    @classmethod
    def rule_set(cls):
        ruleset = {
            'admission.check_copyright': rules.always_allow,
            'admission.sign_diploma': rules.always_allow,
        }
        return RuleSet(ruleset)
