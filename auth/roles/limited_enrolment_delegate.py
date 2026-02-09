# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db.models import UniqueConstraint
from django.utils.translation import gettext_lazy as _
from rules import RuleSet

from admission.auth.predicates.general import is_contingent_non_resident
from osis_role.contrib.models import RoleModel


class LimitedEnrolmentDelegate(RoleModel):
    """
    Délégué.e des formations contingentées

    A accès à tout en lecture et en mode édition uniquement à la zone de commentaire qui lui est spécifique
    """

    class Meta:
        verbose_name = _("Role: Limited enrolment delegate")
        verbose_name_plural = _("Role: Limited enrolment delegate")
        group_name = "limited_enrolment_delegate"
        constraints = [
            UniqueConstraint(fields=['person'], name='admission_unique_limited_enrolment_delegate_by_person')
        ]

    @classmethod
    def rule_set(cls):
        ruleset = {
            'admission.view_enrolment_applications': rules.always_allow,
            'admission.checklist_change_limited_enrolment_delegate_comment': rules.always_allow,
            'admission.view_enrolment_application': is_contingent_non_resident,
            'admission.view_admission_person': is_contingent_non_resident,
            'admission.view_admission_coordinates': is_contingent_non_resident,
            'admission.view_admission_training_choice': is_contingent_non_resident,
            'admission.view_admission_languages': is_contingent_non_resident,
            'admission.view_admission_secondary_studies': is_contingent_non_resident,
            'admission.view_admission_exam': is_contingent_non_resident,
            'admission.view_admission_curriculum': is_contingent_non_resident,
        }
        return RuleSet(ruleset)
