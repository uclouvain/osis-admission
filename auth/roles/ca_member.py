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
from django.utils.translation import gettext_lazy as _
from rules import RuleSet

from admission.auth.predicates import is_part_of_committee_and_invited, is_part_of_committee
from osis_role.contrib.models import EntityRoleModel


class CommitteeMember(EntityRoleModel):
    class Meta:
        verbose_name = _("Committee member")
        verbose_name_plural = _("Committee members")
        group_name = "committee_members"

    @classmethod
    def rule_set(cls):
        return RuleSet({
            'admission.approve_jury': is_part_of_committee,
            'admission.view_doctorateadmission': is_part_of_committee,
            'admission.access_doctorateadmission': rules.always_allow,
            'admission.view_doctorateadmission_person': rules.always_allow,
            'admission.view_doctorateadmission_coordinates': rules.always_allow,
            'admission.view_doctorateadmission_secondary_studies': rules.always_allow,
            'admission.view_doctorateadmission_curriculum': rules.always_allow,
            'admission.view_doctorateadmission_project': is_part_of_committee,
            'admission.view_doctorateadmission_cotutelle': is_part_of_committee,
            'admission.view_doctorateadmission_supervision': is_part_of_committee,
            'admission.approve_proposition': is_part_of_committee_and_invited,
        })
