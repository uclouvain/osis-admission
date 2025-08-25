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
    is_admission_request_promoter,
    is_being_enrolled,
    is_part_of_committee_and_invited,
)
from osis_role.contrib.models import RoleModel


class Promoter(RoleModel):
    """
    Promoteur

    Le promoteur intervient dans plusieurs processus.
    Un promoteur peut être dit "de référence" pour un doctorat donné, il a alors des actions supplémentaires
    à réaliser (spécifier l'institut de la thèse, donner son accord sur les activités de formation doctorale, etc.).
    """

    class Meta:
        verbose_name = _("Role: Supervisor")
        verbose_name_plural = _("Role: Supervisors")
        group_name = "promoters"
        constraints = [
            UniqueConstraint(fields=['person'], name='admission_unique_promoter_by_person'),
        ]

    @classmethod
    def rule_set(cls):
        rules = {
            'admission.api_view_doctorateadmission': is_admission_request_promoter,
            'admission.api_download_pdf_confirmation': is_admission_request_promoter,
            'admission.api_approve_confirmation_paper': is_admission_request_promoter,
            'admission.api_validate_doctoral_training': is_admission_request_promoter,
            'admission.api_fill_thesis': is_admission_request_promoter,
            'admission.api_check_publication_authorisation': is_admission_request_promoter,
            # A promoter can view as long as he is one of the admission promoters and the registration is ongoing
            'admission.api_view_admission_person': is_admission_request_promoter & is_being_enrolled,
            'admission.api_view_admission_coordinates': is_admission_request_promoter & is_being_enrolled,
            'admission.api_view_admission_secondary_studies': is_admission_request_promoter & is_being_enrolled,
            'admission.api_view_admission_exam': is_admission_request_promoter & is_being_enrolled,
            'admission.api_view_admission_languages': is_admission_request_promoter & is_being_enrolled,
            'admission.api_view_admission_curriculum': is_admission_request_promoter & is_being_enrolled,
            'admission.api_view_admission_accounting': is_admission_request_promoter & is_being_enrolled,
            # A promoter can view as long as he is one of the admission promoters
            'admission.api_view_admission_project': is_admission_request_promoter,
            'admission.api_view_admission_training_choice': is_admission_request_promoter,
            'admission.api_view_admission_cotutelle': is_admission & is_admission_request_promoter,
            'admission.api_view_admission_supervision': is_admission_request_promoter,
            'admission.api_view_admission_jury': is_admission_request_promoter,
            # A promoter can approve as long as he is invited to the admission committee
            'admission.api_approve_proposition': is_part_of_committee_and_invited,
        }
        return RuleSet(rules)
