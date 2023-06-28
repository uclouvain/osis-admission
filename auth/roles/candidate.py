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
from rules import RuleSet
from django.utils.translation import gettext_lazy as _

from admission.auth.predicates import (
    complementary_training_enabled,
    is_pre_admission,
    signing_in_progress,
    in_progress,
    unconfirmed_proposition,
    is_admission_request_author,
    is_being_enrolled,
    is_enrolled,
    confirmation_paper_in_progress,
    is_invited_to_complete,
    is_jury_in_progress,
)
from osis_role.contrib.models import RoleModel


author_and_enrolled = is_admission_request_author & is_enrolled

_CANDIDATE_RULESET = {
    # Doctorate
    # A candidate can view as long as it's the author
    'view_doctorateadmission': is_admission_request_author,
    'view_admission_project': is_admission_request_author,
    'view_admission_cotutelle': is_admission_request_author,
    'view_admission_supervision': is_admission_request_author,
    'view_admission_jury': is_admission_request_author,
    'view_admission_training_choice': is_admission_request_author,
    'download_doctorateadmission_pdf_recap': is_admission_request_author,
    # A candidate can view as long as he's the author and he is being enrolled
    'view_admission_person': is_admission_request_author & is_being_enrolled,
    'view_admission_coordinates': is_admission_request_author & is_being_enrolled,
    'view_admission_curriculum': is_admission_request_author & is_being_enrolled,
    'view_admission_secondary_studies': is_admission_request_author & is_being_enrolled,
    'view_admission_languages': is_admission_request_author & is_being_enrolled,
    'view_admission_accounting': is_admission_request_author & is_being_enrolled,
    # Can edit while not confirmed proposition
    'delete_doctorateadmission': is_admission_request_author & unconfirmed_proposition,
    'change_doctorateadmission': is_admission_request_author & unconfirmed_proposition,
    'change_admission_person': is_admission_request_author & unconfirmed_proposition,
    'change_admission_coordinates': is_admission_request_author & unconfirmed_proposition,
    'change_admission_curriculum': is_admission_request_author & unconfirmed_proposition,
    'change_admission_secondary_studies': is_admission_request_author & unconfirmed_proposition,
    'change_admission_languages': is_admission_request_author & unconfirmed_proposition,
    'change_admission_accounting': is_admission_request_author & unconfirmed_proposition,
    # Can edit while the jury is not submitted
    'change_admission_jury': is_admission_request_author & is_jury_in_progress,
    # Project tabs and supervision group edition are accessible as long as signing has not begun
    'change_admission_training_choice': is_admission_request_author & in_progress,
    'change_admission_project': is_admission_request_author & in_progress,
    'change_admission_cotutelle': is_admission_request_author & in_progress,
    'change_admission_supervision': is_admission_request_author & in_progress,
    'request_signatures': is_admission_request_author & in_progress,
    'add_supervision_member': is_admission_request_author & in_progress,
    'remove_supervision_member': is_admission_request_author & in_progress,
    'edit_external_supervision_member': is_admission_request_author & in_progress,
    'set_reference_promoter': is_admission_request_author & unconfirmed_proposition,
    # Once supervision group is signing, he can
    'approve_proposition_by_pdf': is_admission_request_author & signing_in_progress,
    'resend_external_invitation': is_admission_request_author & signing_in_progress,
    'submit_doctorateadmission': is_admission_request_author & unconfirmed_proposition,
    # Once the candidate is enrolling, he can
    'view_admission_confirmation': author_and_enrolled,
    'view_doctoral_training': author_and_enrolled & ~is_pre_admission,
    'view_complementary_training': author_and_enrolled & complementary_training_enabled,
    'view_course_enrollment': author_and_enrolled,
    'add_training': author_and_enrolled,
    'update_training': author_and_enrolled,
    'submit_training': author_and_enrolled,
    'view_training': author_and_enrolled,
    'delete_training': author_and_enrolled,
    # Once the confirmation paper is in progress, he can
    'change_admission_confirmation': is_admission_request_author & confirmation_paper_in_progress,
    'change_admission_confirmation_extension': is_admission_request_author & confirmation_paper_in_progress,
    # Future
    'download_pdf_confirmation': is_admission_request_author,
    'upload_pdf_confirmation': is_admission_request_author,
    'fill_thesis': is_admission_request_author,
    'upload_publication_authorisation': is_admission_request_author,
    # General admission
    # A candidate can view as long as he's the author
    'view_generaleducationadmission': is_admission_request_author,
    'view_generaleducationadmission_person': is_admission_request_author,
    'view_generaleducationadmission_coordinates': is_admission_request_author,
    'view_generaleducationadmission_curriculum': is_admission_request_author,
    'view_generaleducationadmission_secondary_studies': is_admission_request_author,
    'view_generaleducationadmission_languages': is_admission_request_author,
    'view_generaleducationadmission_accounting': is_admission_request_author,
    'view_generaleducationadmission_specific_question': is_admission_request_author,
    'download_generaleducationadmission_pdf_recap': is_admission_request_author,
    # A candidate can edit some tabs as long as the proposition is in progress
    'change_generaleducationadmission_training_choice': is_admission_request_author & in_progress,
    'change_generaleducationadmission_person': is_admission_request_author & in_progress,
    'change_generaleducationadmission_coordinates': is_admission_request_author & in_progress,
    'change_generaleducationadmission_curriculum': is_admission_request_author & in_progress,
    'change_generaleducationadmission_secondary_studies': is_admission_request_author & in_progress,
    'change_generaleducationadmission_languages': is_admission_request_author & in_progress,
    'change_generaleducationadmission_accounting': is_admission_request_author & in_progress,
    'change_generaleducationadmission_specific_question': is_admission_request_author & in_progress,
    'change_generaleducationadmission': is_admission_request_author & in_progress,
    'delete_generaleducationadmission': is_admission_request_author & in_progress,
    'submit_generaleducationadmission': is_admission_request_author & in_progress,
    # A candidate can edit some tabs after the proposition has been submitted
    'view_generaleducationadmission_documents': is_admission_request_author & is_invited_to_complete,
    'change_generaleducationadmission_documents': is_admission_request_author & is_invited_to_complete,
    # Continuing admission
    # A candidate can view as long as he's the author
    'view_continuingeducationadmission': is_admission_request_author,
    'view_continuingeducationadmission_person': is_admission_request_author,
    'view_continuingeducationadmission_coordinates': is_admission_request_author,
    'view_continuingeducationadmission_curriculum': is_admission_request_author,
    'view_continuingeducationadmission_secondary_studies': is_admission_request_author,
    'view_continuingeducationadmission_languages': is_admission_request_author,
    'view_continuingeducationadmission_specific_question': is_admission_request_author,
    'download_continuingeducationadmission_pdf_recap': is_admission_request_author,
    # A candidate can edit some tabs as long as the proposition is in progress
    'change_continuingeducationadmission_training_choice': is_admission_request_author & in_progress,
    'change_continuingeducationadmission_person': is_admission_request_author & in_progress,
    'change_continuingeducationadmission_coordinates': is_admission_request_author & in_progress,
    'change_continuingeducationadmission_curriculum': is_admission_request_author & in_progress,
    'change_continuingeducationadmission_secondary_studies': is_admission_request_author & in_progress,
    'change_continuingeducationadmission_languages': is_admission_request_author & in_progress,
    'delete_continuingeducationadmission': is_admission_request_author & in_progress,
    'submit_continuingeducationadmission': is_admission_request_author & in_progress,
    'change_continuingeducationadmission_specific_question': is_admission_request_author & in_progress,
}


class Candidate(RoleModel):
    class Meta:
        verbose_name = _("Role: Candidate")
        verbose_name_plural = _("Role: Candidates")
        group_name = "candidates"

    @classmethod
    def rule_set(cls):
        return RuleSet({f'admission.{perm_name}': rule for perm_name, rule in _CANDIDATE_RULESET.items()})
