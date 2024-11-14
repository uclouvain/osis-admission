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
from django.db.models import UniqueConstraint
from django.utils.translation import gettext_lazy as _
from rules import RuleSet

from admission.auth.predicates import common, continuing, doctorate, general
from osis_role.contrib.models import RoleModel

author_and_enrolled = common.is_admission_request_author & doctorate.is_enrolled

_CANDIDATE_RULESET = {
    # Doctorate
    # A candidate can view as long as it's the author
    'view_doctorateadmission': common.is_admission_request_author,
    'view_admission_jury': author_and_enrolled,
    'download_doctorateadmission_pdf_recap': common.is_admission_request_author,
    # A candidate can view as long as he's the author and the proposition is not confirmed
    'view_admission_person': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'view_admission_coordinates': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'view_admission_curriculum': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'view_admission_secondary_studies': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'view_admission_languages': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'view_admission_accounting': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'view_admission_training_choice': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'view_admission_project': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'view_admission_cotutelle': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'view_admission_supervision': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    # Can edit while not confirmed proposition
    'delete_doctorateadmission': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'change_doctorateadmission': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'change_admission_person': common.is_admission_request_author
    & doctorate.unconfirmed_proposition
    & common.does_not_have_a_submitted_admission,
    'change_admission_coordinates': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'change_admission_curriculum': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'change_admission_secondary_studies': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'change_admission_languages': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    'change_admission_accounting': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    # Can edit while the jury is not submitted
    'change_admission_jury': author_and_enrolled & doctorate.is_jury_in_progress,
    # Project tabs and supervision group edition are accessible as long as signing has not begun
    'change_admission_training_choice': common.is_admission_request_author & doctorate.in_progress,
    'change_admission_project': common.is_admission_request_author & doctorate.in_progress,
    'change_admission_cotutelle': common.is_admission_request_author & doctorate.in_progress,
    'change_admission_supervision': common.is_admission_request_author & doctorate.in_progress,
    'request_signatures': common.is_admission_request_author & doctorate.in_progress,
    'add_supervision_member': common.is_admission_request_author & doctorate.in_progress,
    'remove_supervision_member': common.is_admission_request_author & doctorate.in_progress,
    'edit_external_supervision_member': common.is_admission_request_author & doctorate.in_progress,
    'set_reference_promoter': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    # Once supervision group is signing, he can
    'approve_proposition_by_pdf': common.is_admission_request_author & doctorate.signing_in_progress,
    'resend_external_invitation': common.is_admission_request_author & doctorate.signing_in_progress,
    'submit_doctorateadmission': common.is_admission_request_author & doctorate.unconfirmed_proposition,
    # A candidate can edit some tabs after the proposition has been submitted
    'view_admission_documents': common.is_admission_request_author & doctorate.is_invited_to_complete,
    'change_admission_documents': common.is_admission_request_author & doctorate.is_invited_to_complete,
    # Once the candidate is enrolling, he can
    'view_admission_confirmation': author_and_enrolled,
    'view_doctoral_training': author_and_enrolled & ~doctorate.is_pre_admission,
    'view_complementary_training': author_and_enrolled & doctorate.complementary_training_enabled,
    'view_course_enrollment': author_and_enrolled,
    'add_training': author_and_enrolled,
    'update_training': author_and_enrolled,
    'submit_training': author_and_enrolled,
    'view_training': author_and_enrolled,
    'delete_training': author_and_enrolled,
    # Once the confirmation paper is in progress, he can
    'change_admission_confirmation': common.is_admission_request_author & doctorate.confirmation_paper_in_progress,
    'change_admission_confirmation_extension': common.is_admission_request_author
    & doctorate.confirmation_paper_in_progress,
    # Future
    'download_pdf_confirmation': common.is_admission_request_author,
    'upload_pdf_confirmation': common.is_admission_request_author,
    'fill_thesis': common.is_admission_request_author,
    'upload_publication_authorisation': common.is_admission_request_author,
    # General admission
    # A candidate can view as long as he's the author
    'view_generaleducationadmission': common.is_admission_request_author,
    'view_generaleducationadmission_person': common.is_admission_request_author & general.in_progress,
    'view_generaleducationadmission_training_choice': common.is_admission_request_author & general.in_progress,
    'view_generaleducationadmission_coordinates': common.is_admission_request_author & general.in_progress,
    'view_generaleducationadmission_curriculum': common.is_admission_request_author & general.in_progress,
    'view_generaleducationadmission_secondary_studies': common.is_admission_request_author & general.in_progress,
    'view_generaleducationadmission_languages': common.is_admission_request_author & general.in_progress,
    'view_generaleducationadmission_accounting': common.is_admission_request_author & general.in_progress,
    'view_generaleducationadmission_specific_question': common.is_admission_request_author & general.in_progress,
    'view_generaleducationadmission_fees': common.is_admission_request_author & general.can_view_payment,
    'download_generaleducationadmission_pdf_recap': common.is_admission_request_author,
    # A candidate can edit some tabs as long as the proposition is in progress
    'change_generaleducationadmission_training_choice': common.is_admission_request_author & general.in_progress,
    'change_generaleducationadmission_person': common.is_admission_request_author
    & general.in_progress
    & common.does_not_have_a_submitted_admission,
    'change_generaleducationadmission_coordinates': common.is_admission_request_author & general.in_progress,
    'change_generaleducationadmission_curriculum': common.is_admission_request_author & general.in_progress,
    'change_generaleducationadmission_secondary_studies': common.is_admission_request_author & general.in_progress,
    'change_generaleducationadmission_languages': common.is_admission_request_author & general.in_progress,
    'change_generaleducationadmission_accounting': common.is_admission_request_author & general.in_progress,
    'change_generaleducationadmission_specific_question': common.is_admission_request_author & general.in_progress,
    'change_generaleducationadmission': common.is_admission_request_author & general.in_progress,
    'delete_generaleducationadmission': common.is_admission_request_author & general.in_progress,
    'submit_generaleducationadmission': common.is_admission_request_author & general.in_progress,
    # A candidate can edit some tabs after the proposition has been submitted
    'view_generaleducationadmission_documents': common.is_admission_request_author & general.is_invited_to_complete,
    'change_generaleducationadmission_documents': common.is_admission_request_author & general.is_invited_to_complete,
    'pay_generaleducationadmission_fees': common.is_admission_request_author
    & general.is_invited_to_pay_after_submission,
    'pay_generaleducationadmission_fees_after_request': common.is_admission_request_author
    & general.is_invited_to_pay_after_request,
    # Continuing admission
    # A candidate can view as long as he's the author
    'view_continuingeducationadmission': common.is_admission_request_author,
    'view_continuingeducationadmission_person': common.is_admission_request_author & continuing.in_progress,
    'view_continuingeducationadmission_training_choice': common.is_admission_request_author & continuing.in_progress,
    'view_continuingeducationadmission_coordinates': common.is_admission_request_author & continuing.in_progress,
    'view_continuingeducationadmission_curriculum': common.is_admission_request_author & continuing.in_progress,
    'view_continuingeducationadmission_secondary_studies': common.is_admission_request_author & continuing.in_progress,
    'view_continuingeducationadmission_languages': common.is_admission_request_author & continuing.in_progress,
    'view_continuingeducationadmission_specific_question': common.is_admission_request_author & continuing.in_progress,
    'download_continuingeducationadmission_pdf_recap': common.is_admission_request_author,
    # A candidate can edit some tabs as long as the proposition is in progress
    'change_continuingeducationadmission_training_choice': common.is_admission_request_author & continuing.in_progress,
    'change_continuingeducationadmission_person': common.is_admission_request_author
    & continuing.in_progress
    & common.does_not_have_a_submitted_admission,
    'change_continuingeducationadmission_coordinates': common.is_admission_request_author & continuing.in_progress,
    'change_continuingeducationadmission_curriculum': common.is_admission_request_author & continuing.in_progress,
    'change_continuingeducationadmission_secondary_studies': common.is_admission_request_author
    & continuing.in_progress,
    'change_continuingeducationadmission_languages': common.is_admission_request_author & continuing.in_progress,
    'delete_continuingeducationadmission': common.is_admission_request_author & continuing.in_progress,
    'submit_continuingeducationadmission': common.is_admission_request_author & continuing.in_progress,
    'change_continuingeducationadmission_specific_question': common.is_admission_request_author
    & continuing.in_progress,
    # A candidate can edit some tabs after the proposition has been submitted
    'view_continuingeducationadmission_documents': common.is_admission_request_author
    & continuing.is_invited_to_complete,
    'change_continuingeducationadmission_documents': common.is_admission_request_author
    & continuing.is_invited_to_complete,
}


class Candidate(RoleModel):
    class Meta:
        constraints = [
            UniqueConstraint(fields=['person'], name='unique_candidate'),
        ]
        verbose_name = _("Role: Candidate")
        verbose_name_plural = _("Role: Candidates")
        group_name = "candidates"

    @classmethod
    def rule_set(cls):
        return RuleSet({f'admission.{perm_name}': rule for perm_name, rule in _CANDIDATE_RULESET.items()})
