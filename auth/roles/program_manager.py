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
from django.db import models
from django.utils.translation import gettext_lazy as _

from admission.auth.predicates import continuing, doctorate, general
from admission.auth.predicates.common import (
    candidate_has_other_doctorate_or_general_admissions,
    has_education_group_of_types,
    is_debug,
    is_part_of_education_group,
    is_sent_to_epc,
    past_experiences_checklist_tab_is_not_sufficient,
    personal_data_checklist_status_is_cleaned,
    personal_data_checklist_status_is_not_validated,
    personal_data_checklist_status_is_to_be_processed,
    workflow_injection_signaletique_en_cours,
)
from admission.infrastructure.admission.shared_kernel.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.models.education_group import EducationGroup
from education_group.contrib.models import EducationGroupRoleModel


class ProgramManager(EducationGroupRoleModel):
    """
    Gestionnaire d'admission d'un programme

    Intervient dans le processus d'admission. Accès aux demandes des 3 contextes (général, doctorat, iufc) via
    l'affection aux formations.
    Autres noms "contextualisés" donnés à ces personnes : Gestionnaire CDD, Gestionnaire Facultaire.
    """

    education_group = models.ForeignKey(EducationGroup, on_delete=models.CASCADE, related_name='+')

    def __str__(self):  # pragma: no cover
        return f"{self.person} - {self.education_group}"

    @property
    def education_group_most_recent_acronym(self):  # pragma: no cover
        return self.education_group.most_recent_acronym

    class Meta:
        verbose_name = _("Role: Program manager")
        verbose_name_plural = _("Role: Program managers")
        group_name = "admission_program_managers"
        unique_together = ('person', 'education_group')

    @classmethod
    def rule_set(cls):
        ruleset = {
            # Listings
            'admission.view_enrolment_applications': has_education_group_of_types(
                *AnneeInscriptionFormationTranslator.GENERAL_EDUCATION_TYPES,
            ),
            'admission.view_doctorate_enrolment_applications': has_education_group_of_types(
                *AnneeInscriptionFormationTranslator.DOCTORATE_EDUCATION_TYPES,
            ),
            'admission.view_continuing_enrolment_applications': has_education_group_of_types(
                *AnneeInscriptionFormationTranslator.CONTINUING_EDUCATION_TYPES,
            ),
            # Access a single application
            'admission.view_enrolment_application': is_part_of_education_group,
            # Profile
            'admission.view_admission_person': is_part_of_education_group,
            'admission.change_admission_person': is_part_of_education_group
            & (
                general.in_manager_status & personal_data_checklist_status_is_not_validated
                | continuing.in_manager_status & ~candidate_has_other_doctorate_or_general_admissions
                | doctorate.in_manager_status & personal_data_checklist_status_is_not_validated
            )
            & ~is_sent_to_epc
            & ~workflow_injection_signaletique_en_cours,
            'admission.view_admission_coordinates': is_part_of_education_group,
            'admission.change_admission_coordinates': is_part_of_education_group
            & (
                general.in_manager_status & personal_data_checklist_status_is_not_validated
                | continuing.in_manager_status
                | doctorate.in_manager_status & personal_data_checklist_status_is_not_validated
            )
            & ~is_sent_to_epc
            & ~workflow_injection_signaletique_en_cours,
            'admission.view_admission_secondary_studies': is_part_of_education_group,
            'admission.view_admission_exam': is_part_of_education_group,
            'admission.change_admission_secondary_studies': is_part_of_education_group
            & continuing.in_manager_status
            & ~is_sent_to_epc
            & ~candidate_has_other_doctorate_or_general_admissions,
            'admission.change_admission_exam': is_part_of_education_group
            & continuing.in_manager_status
            & ~is_sent_to_epc
            & ~candidate_has_other_doctorate_or_general_admissions,
            'admission.view_admission_languages': is_part_of_education_group,
            'admission.change_admission_languages': is_part_of_education_group
            & doctorate.in_fac_status
            & ~is_sent_to_epc,
            'admission.view_admission_curriculum': is_part_of_education_group,
            'admission.change_admission_global_curriculum': is_part_of_education_group
            & (continuing.in_manager_status | doctorate.in_fac_status)
            & ~is_sent_to_epc,
            'admission.change_admission_curriculum': is_part_of_education_group
            & (
                (continuing.in_manager_status & ~candidate_has_other_doctorate_or_general_admissions)
                | doctorate.in_fac_status
            )
            & ~is_sent_to_epc,
            'admission.delete_admission_curriculum': is_part_of_education_group
            & continuing.in_manager_status
            & ~is_sent_to_epc
            & ~candidate_has_other_doctorate_or_general_admissions,
            # Project
            'admission.view_admission_project': is_part_of_education_group,
            'admission.send_back_to_candidate': is_part_of_education_group
            & doctorate.signing_in_progress_before_submition
            & ~is_sent_to_epc,
            'admission.change_admission_project': is_part_of_education_group & doctorate.is_submitted & ~is_sent_to_epc,
            'admission.view_admission_cotutelle': doctorate.is_admission & is_part_of_education_group,
            'admission.change_admission_cotutelle': doctorate.is_admission
            & is_part_of_education_group
            & doctorate.is_submitted
            & ~is_sent_to_epc,
            'admission.view_admission_training_choice': is_part_of_education_group,
            'admission.change_admission_training_choice': is_part_of_education_group
            & (continuing.in_manager_status | doctorate.in_fac_status)
            & ~is_sent_to_epc
            & ~workflow_injection_signaletique_en_cours,
            'admission.view_admission_accounting': is_part_of_education_group,
            'admission.view_admission_specific_questions': is_part_of_education_group,
            'admission.change_admission_specific_questions': is_part_of_education_group
            & continuing.in_manager_status
            & ~is_sent_to_epc,
            # Supervision
            'admission.view_admission_supervision': is_part_of_education_group,
            'admission.change_admission_supervision': is_part_of_education_group
            & doctorate.is_submitted
            & ~is_sent_to_epc,
            'admission.add_supervision_member': is_part_of_education_group & doctorate.is_submitted & ~is_sent_to_epc,
            'admission.set_reference_promoter': is_part_of_education_group,
            'admission.remove_supervision_member': is_part_of_education_group
            & doctorate.is_submitted
            & ~is_sent_to_epc,
            'admission.edit_external_supervision_member': is_part_of_education_group
            & doctorate.is_submitted
            & ~is_sent_to_epc,
            'admission.approve_proposition_by_pdf': is_part_of_education_group & doctorate.is_submitted,
            'admission.resend_invitation': is_part_of_education_group & doctorate.signing_in_progress,
            'admission.request_signatures': is_part_of_education_group & doctorate.is_submitted,
            'admission.view_historyentry': is_part_of_education_group,
            # Management
            'admission.add_internalnote': is_part_of_education_group & ~is_sent_to_epc,
            'admission.view_internalnote': is_part_of_education_group,
            'admission.view_documents_management': is_part_of_education_group
            & (general.is_submitted | continuing.is_submitted_or_not_cancelled | doctorate.not_cancelled),
            'admission.edit_documents': is_part_of_education_group
            & (general.is_submitted | continuing.not_cancelled | doctorate.is_submitted)
            & ~is_sent_to_epc,
            'admission.request_documents': is_part_of_education_group
            & (general.in_fac_status | continuing.can_request_documents | doctorate.in_fac_status)
            & ~is_sent_to_epc,
            'admission.cancel_document_request': is_part_of_education_group
            & (
                general.in_fac_document_request_status
                | continuing.in_document_request_status
                | doctorate.in_fac_document_request_status
            )
            & ~is_sent_to_epc,
            'admission.generate_in_progress_analysis_folder': is_part_of_education_group
            & (continuing.in_progress | doctorate.in_progress | doctorate.signing_in_progress_before_submition),
            'admission.view_checklist': is_part_of_education_group
            & (general.is_submitted | continuing.is_submitted | doctorate.is_submitted),
            'admission.change_checklist': is_part_of_education_group
            & continuing.is_continuing
            & continuing.is_submitted
            & ~is_sent_to_epc,
            'admission.change_personal_data_checklist_status_to_be_processed': is_part_of_education_group
            & (general.in_manager_status | doctorate.in_manager_status)
            & personal_data_checklist_status_is_cleaned
            & ~is_sent_to_epc,
            'admission.change_personal_data_checklist_status_cleaned': is_part_of_education_group
            & (general.in_manager_status | doctorate.in_manager_status)
            & personal_data_checklist_status_is_to_be_processed
            & ~is_sent_to_epc,
            'admission.cancel_admission_iufc': is_part_of_education_group
            & continuing.is_submitted
            & ~continuing.is_validated
            & ~is_sent_to_epc,
            'admission.checklist_change_training_choice': is_part_of_education_group
            & doctorate.in_fac_status
            & ~is_sent_to_epc,
            'admission.checklist_change_faculty_decision': is_part_of_education_group
            & (general.in_fac_status | doctorate.in_fac_status)
            & ~is_sent_to_epc,
            'admission.checklist_faculty_decision_transfer_to_sic_with_decision': is_part_of_education_group
            & (general.in_fac_status | doctorate.in_fac_status)
            & ~is_sent_to_epc,
            'admission.checklist_faculty_decision_transfer_to_sic_without_decision': is_part_of_education_group
            & (general.in_fac_status | doctorate.in_fac_status)
            & ~is_sent_to_epc,
            'admission.checklist_select_access_title': is_part_of_education_group
            & (general.in_fac_status | doctorate.in_fac_status)
            & past_experiences_checklist_tab_is_not_sufficient
            & ~is_sent_to_epc,
            'admission.checklist_change_fac_comment': is_part_of_education_group & ~is_sent_to_epc,
            'admission.checklist_financability_dispensation_fac': is_part_of_education_group
            & (general.in_fac_status | general.can_send_to_fac_faculty_decision)
            & ~is_sent_to_epc,
            'admission.continuing_checklist_change_fac_comment': is_part_of_education_group & ~is_sent_to_epc,
            'admission.checklist_change_comment': is_part_of_education_group
            & continuing.is_continuing
            & ~is_sent_to_epc,
            'admission.view_debug_info': is_part_of_education_group & is_debug,
            'admission.send_message': is_part_of_education_group,
            # Exports
            'admission.download_doctorateadmission_pdf_recap': is_part_of_education_group,
        }
        return rules.RuleSet(ruleset)
