# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import rules
from rules import RuleSet
from django.utils.translation import gettext_lazy as _

from osis_role.contrib.models import EntityRoleModel


class SicManager(EntityRoleModel):
    class Meta:
        verbose_name = _("SIC manager")
        verbose_name_plural = _("SIC managers")
        group_name = "sic_managers"

    @classmethod
    def rule_set(cls):
        return RuleSet({
            'admission.change_doctorateadmission': rules.always_allow,
            'admission.delete_doctorateadmission': rules.always_deny,
            'admission.access_doctorateadmission': rules.always_allow,
            'admission.appose_sic_notice': rules.always_allow,
        })
