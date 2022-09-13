# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from rules import RuleSet
from django.utils.translation import gettext_lazy as _

from admission.auth.predicates import (
    signing_in_progress,
    in_progress,
    unconfirmed_proposition,
    is_admission_request_author,
    is_being_enrolled,
    is_enrolled,
    confirmation_paper_in_progress,
)
from osis_role.contrib.models import RoleModel


class Candidate(RoleModel):
    class Meta:
        verbose_name = _("Candidate")
        verbose_name_plural = _("Candidates")
        group_name = "candidates"

    @classmethod
    def rule_set(cls):
        ruleset = {
            # A candidate can view as long as it's the author
            'admission.view_doctorateadmission': is_admission_request_author,
            'admission.view_doctorateadmission_project': is_admission_request_author,
            'admission.view_doctorateadmission_cotutelle': is_admission_request_author,
            'admission.view_doctorateadmission_supervision': is_admission_request_author,
            # A candidate can view as long as he's the author and he is being enrolled
            'admission.view_doctorateadmission_person': is_admission_request_author & is_being_enrolled,
            'admission.view_doctorateadmission_coordinates': is_admission_request_author & is_being_enrolled,
            'admission.view_doctorateadmission_curriculum': is_admission_request_author & is_being_enrolled,
            'admission.view_doctorateadmission_secondary_studies': is_admission_request_author & is_being_enrolled,
            'admission.view_doctorateadmission_languages': is_admission_request_author & is_being_enrolled,
            'admission.view_accounting': is_admission_request_author & is_being_enrolled,
            # Can edit while not confirmed proposition
            'admission.delete_doctorateadmission': is_admission_request_author & unconfirmed_proposition,
            'admission.change_doctorateadmission': is_admission_request_author & unconfirmed_proposition,
            'admission.change_doctorateadmission_person': is_admission_request_author & unconfirmed_proposition,
            'admission.change_doctorateadmission_coordinates': is_admission_request_author & unconfirmed_proposition,
            'admission.change_doctorateadmission_curriculum': is_admission_request_author & unconfirmed_proposition,
            'admission.change_doctorateadmission_secondary_studies': is_admission_request_author
            & unconfirmed_proposition,
            'admission.change_doctorateadmission_languages': is_admission_request_author & unconfirmed_proposition,
            'admission.change_accounting': is_admission_request_author & unconfirmed_proposition,
            # Project tabs and supervision group edition are accessible as long as signing has not begun
            'admission.change_doctorateadmission_project': is_admission_request_author & in_progress,
            'admission.change_doctorateadmission_cotutelle': is_admission_request_author & in_progress,
            'admission.change_doctorateadmission_supervision': is_admission_request_author & in_progress,
            'admission.request_signatures': is_admission_request_author & in_progress,
            'admission.add_supervision_member': is_admission_request_author & in_progress,
            'admission.remove_supervision_member': is_admission_request_author & in_progress,
            'admission.set_reference_promoter': is_admission_request_author & unconfirmed_proposition,
            # Once supervision group is signing, he can
            'admission.approve_proposition_by_pdf': is_admission_request_author & signing_in_progress,
            'admission.submit_doctorateadmission': is_admission_request_author & signing_in_progress,
            # Once the candidate is enrolling, he can
            'admission.view_doctorateadmission_confirmation': is_admission_request_author & is_enrolled,
            'admission.view_doctorateadmission_doctoral_training': is_admission_request_author & is_enrolled,
            'admission.add_doctorateadmission_doctoral_training': is_admission_request_author & is_enrolled,
            'admission.submit_doctorateadmission_doctoral_training': is_admission_request_author & is_enrolled,
            'admission.delete_doctorateadmission_doctoral_training': is_admission_request_author & is_enrolled,
            # Once the confirmation paper is in progress, he can
            'admission.change_doctorateadmission_confirmation': is_admission_request_author
            & confirmation_paper_in_progress,
            'admission.change_doctorateadmission_confirmation_extension': is_admission_request_author
            & confirmation_paper_in_progress,
            # Future
            'admission.download_pdf_confirmation': is_admission_request_author,
            'admission.upload_pdf_confirmation': is_admission_request_author,
            'admission.fill_thesis': is_admission_request_author,
            'admission.upload_publication_authorisation': is_admission_request_author,
        }
        return RuleSet(ruleset)
