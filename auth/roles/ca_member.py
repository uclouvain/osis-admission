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
from django.db.models import UniqueConstraint
from django.utils.translation import gettext_lazy as _
from rules import RuleSet

from admission.auth.predicates.doctorate import (
    is_admission,
    is_being_enrolled,
    is_enrolled,
    is_part_of_committee,
    is_part_of_committee_and_invited,
)
from osis_role.contrib.models import RoleModel


class CommitteeMember(RoleModel):
    """
    Membre du comité

    Membre du comité d'accompagnement du doctorand, il approuve l'admission et le Jury. Dans d'autres processus
    c'est la CDD ou le promoteur qui acte la décision collégiale du comité d'accompagnement dans le système.
    """

    class Meta:
        verbose_name = _("Role: Committee member")
        verbose_name_plural = _("Role: Committee members")
        group_name = "committee_members"
        constraints = [UniqueConstraint(fields=['person'], name='admission_unique_committee_member_by_person')]

    @classmethod
    def rule_set(cls):
        ruleset = {
            'admission.api_approve_jury': is_part_of_committee,
            # A ca member can view as long as he belongs to the committee and the registration is ongoing
            'admission.api_view_admission_person': is_part_of_committee & is_being_enrolled,
            'admission.api_view_admission_coordinates': is_part_of_committee & is_being_enrolled,
            'admission.api_view_admission_secondary_studies': is_part_of_committee & is_being_enrolled,
            'admission.api_view_admission_exam': is_part_of_committee & is_being_enrolled,
            'admission.api_view_admission_languages': is_part_of_committee & is_being_enrolled,
            'admission.api_view_admission_curriculum': is_part_of_committee & is_being_enrolled,
            'admission.api_view_admission_accounting': is_part_of_committee & is_being_enrolled,
            # A ca member can view as long as he belongs to the committee
            'admission.api_view_doctorateadmission': is_part_of_committee,
            'admission.api_view_admission_training_choice': is_part_of_committee,
            'admission.api_view_admission_project': is_part_of_committee,
            'admission.api_view_admission_cotutelle': is_admission & is_part_of_committee,
            'admission.api_view_admission_supervision': is_part_of_committee,
            'admission.api_view_doctorate_management': is_part_of_committee,
            # A ca member can approve as long as he is invited to the committee
            'admission.api_approve_proposition': is_part_of_committee_and_invited,
            # Once the candidate is enrolling, a ca member can
            'admission.api_view_admission_confirmation': is_part_of_committee & is_enrolled,
        }
        return RuleSet(ruleset)
