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
from django.utils.translation import gettext_lazy as _
from rules import RuleSet

from admission.auth.predicates import (
    complementary_training_enabled,
    confirmation_paper_in_progress,
    is_admission_reference_promoter,
    is_admission_request_promoter,
    is_being_enrolled,
    is_enrolled,
    is_part_of_committee_and_invited,
    is_pre_admission,
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
        verbose_name = _("Role: Promoter")
        verbose_name_plural = _("Role: Promoters")
        group_name = "promoters"

    @classmethod
    def rule_set(cls):
        promoter_and_enrolled = is_admission_request_promoter & is_enrolled
        rules = {
            'admission.view_doctorateadmission': is_admission_request_promoter,
            'admission.download_pdf_confirmation': is_admission_request_promoter,
            'admission.approve_confirmation_paper': is_admission_request_promoter,
            'admission.validate_doctoral_training': is_admission_request_promoter,
            'admission.fill_thesis': is_admission_request_promoter,
            'admission.check_publication_authorisation': is_admission_request_promoter,
            # A promoter can view as long as he is one of the admission promoters and the registration is ongoing
            'admission.view_doctorateadmission_person': is_admission_request_promoter & is_being_enrolled,
            'admission.view_doctorateadmission_coordinates': is_admission_request_promoter & is_being_enrolled,
            'admission.view_doctorateadmission_secondary_studies': is_admission_request_promoter & is_being_enrolled,
            'admission.view_doctorateadmission_languages': is_admission_request_promoter & is_being_enrolled,
            'admission.view_doctorateadmission_curriculum': is_admission_request_promoter & is_being_enrolled,
            'admission.view_doctorateadmission_accounting': is_admission_request_promoter & is_being_enrolled,
            # A promoter can view as long as he is one of the admission promoters
            'admission.view_doctorateadmission_project': is_admission_request_promoter,
            'admission.view_doctorateadmission_training_choice': is_admission_request_promoter,
            'admission.view_doctorateadmission_cotutelle': is_admission_request_promoter,
            'admission.view_doctorateadmission_supervision': is_admission_request_promoter,
            # A promoter can approve as long as he is invited to the admission committee
            'admission.approve_proposition': is_part_of_committee_and_invited,
            # Once the candidate is enrolling, a promoter can
            'admission.view_doctorateadmission_confirmation': is_admission_request_promoter & is_enrolled,
            'admission.change_doctorateadmission_confirmation': (
                is_admission_request_promoter & confirmation_paper_in_progress
            ),
            'admission.upload_pdf_confirmation': is_admission_request_promoter & is_enrolled,
            # Doctoral training
            'admission.view_doctoral_training': promoter_and_enrolled & ~is_pre_admission,
            'admission.view_complementary_training': promoter_and_enrolled & complementary_training_enabled,
            'admission.view_course_enrollment': promoter_and_enrolled,
            'admission.view_training': promoter_and_enrolled,
            'admission.assent_training': is_admission_reference_promoter & is_enrolled,
        }
        return RuleSet(rules)
