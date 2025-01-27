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
import rules
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from rules import RuleSet

from admission.auth.predicates import general, continuing, doctorate
from admission.auth.predicates.common import (
    has_scope,
    is_debug,
    is_entity_manager,
    is_sent_to_epc,
    pending_digit_ticket_response,
    past_experiences_checklist_tab_is_not_sufficient,
)
from education_group.auth.scope import Scope
from osis_role.contrib.models import EntityRoleModel


class CentralManager(EntityRoleModel):
    """
    Gestionnaire central d'admission

    Intervient dans le processus d'admission pour donner son accord/désaccord.
    """

    scopes = ArrayField(
        models.CharField(max_length=200, choices=Scope.choices()),
        blank=True,
    )

    class Meta:
        verbose_name = _("Role: Central manager")
        verbose_name_plural = _("Role: Central managers")
        group_name = "admission_central_managers"

    @classmethod
    def rule_set(cls):
        ruleset = {
            # Listings
            'admission.view_enrolment_applications': has_scope(Scope.ALL),
            'admission.view_doctorate_enrolment_applications': has_scope(Scope.DOCTORAT),
            'admission.view_continuing_enrolment_applications': has_scope(Scope.IUFC),
            # Access a single application
            'admission.view_enrolment_application': is_entity_manager,
            'admission.change_doctorateadmission': is_entity_manager,
            'admission.delete_doctorateadmission': is_entity_manager,
            'admission.view_doctorateadmission': is_entity_manager,
            'admission.appose_sic_notice': is_entity_manager,
            'admission.view_admission_person': is_entity_manager,
            'admission.change_admission_person': is_entity_manager
            & (
                general.in_sic_status
                | continuing.in_manager_status
                | doctorate.in_sic_status
                | general.in_progress
                | continuing.in_progress
                | doctorate.in_progress
            )
            & ~is_sent_to_epc
            & ~pending_digit_ticket_response,
            'admission.view_admission_coordinates': is_entity_manager,
            'admission.change_admission_coordinates': is_entity_manager
            & (
                general.in_sic_status
                | continuing.in_manager_status
                | doctorate.in_sic_status
                | general.in_progress
                | continuing.in_progress
                | doctorate.in_progress
            )
            & ~is_sent_to_epc
            & ~pending_digit_ticket_response,
            'admission.view_admission_training_choice': is_entity_manager,
            'admission.change_admission_training_choice': is_entity_manager
            & (general.in_sic_status | continuing.in_manager_status | doctorate.in_sic_status)
            & ~is_sent_to_epc
            & ~pending_digit_ticket_response,
            'admission.view_admission_languages': is_entity_manager,
            'admission.change_admission_languages': is_entity_manager & doctorate.in_sic_status & ~is_sent_to_epc,
            'admission.view_admission_secondary_studies': is_entity_manager,
            'admission.change_admission_secondary_studies': is_entity_manager
            & (general.in_sic_status | continuing.in_manager_status)
            & ~is_sent_to_epc,
            'admission.view_admission_curriculum': is_entity_manager,
            'admission.change_admission_curriculum': is_entity_manager
            & (general.in_sic_status | continuing.in_manager_status | doctorate.in_sic_status)
            & ~is_sent_to_epc,
            'admission.delete_admission_curriculum': is_entity_manager
            & (general.in_sic_status | continuing.in_manager_status | doctorate.in_sic_status)
            & ~is_sent_to_epc,
            'admission.view_admission_project': is_entity_manager,
            'admission.view_admission_cotutelle': doctorate.is_admission & is_entity_manager,
            'admission.view_admission_supervision': is_entity_manager,
            'admission.view_admission_accounting': is_entity_manager,
            'admission.change_admission_accounting': is_entity_manager
            & (general.in_sic_status | doctorate.in_sic_status)
            & ~is_sent_to_epc,
            'admission.view_admission_specific_questions': is_entity_manager,
            'admission.change_admission_specific_questions': is_entity_manager
            & (general.in_sic_status | continuing.in_manager_status)
            & ~is_sent_to_epc,
            'admission.view_admission_jury': is_entity_manager,
            'admission.change_admission_jury': is_entity_manager,
            'admission.view_internalnote': is_entity_manager,
            'admission.view_debug_info': is_entity_manager & is_debug,
            'admission.view_historyentry': is_entity_manager,
            'admission.download_doctorateadmission_pdf_recap': is_entity_manager,
            'admission.view_documents_management': is_entity_manager
            & (general.not_cancelled | continuing.is_submitted_or_not_cancelled | doctorate.not_cancelled),
            'admission.edit_documents': is_entity_manager
            & (general.is_submitted | continuing.not_cancelled | doctorate.is_submitted)
            & ~is_sent_to_epc,
            'admission.request_documents': is_entity_manager
            & (general.in_sic_status | continuing.can_request_documents | doctorate.in_sic_status)
            & ~is_sent_to_epc,
            'admission.cancel_document_request': is_entity_manager
            & (
                general.in_sic_document_request_status
                | continuing.in_document_request_status
                | doctorate.in_sic_document_request_status
            )
            & ~is_sent_to_epc,
            'admission.generate_in_progress_analysis_folder': is_entity_manager
            & (
                (general.is_general & general.in_progress)
                | (continuing.is_continuing & continuing.in_progress)
                | (doctorate.is_doctorate & doctorate.in_progress)
            )
            & ~is_sent_to_epc,
            'admission.view_checklist': is_entity_manager
            & (general.is_submitted | continuing.is_submitted | doctorate.is_submitted),
            'admission.change_checklist': is_entity_manager
            & (general.in_sic_status | continuing.is_submitted | doctorate.in_sic_status)
            & ~is_sent_to_epc,
            'admission.change_checklist_iufc': is_entity_manager & continuing.is_submitted & ~is_sent_to_epc,
            'admission.change_payment': is_entity_manager & general.in_sic_status_or_application_fees & ~is_sent_to_epc,
            'admission.checklist_faculty_decision_transfer_to_fac': is_entity_manager
            & (general.can_send_to_fac_faculty_decision | doctorate.can_send_to_fac_faculty_decision)
            & ~is_sent_to_epc,
            'admission.checklist_faculty_decision_transfer_to_sic_without_decision': is_entity_manager
            & (general.in_fac_status | doctorate.in_fac_status)
            & ~is_sent_to_epc,
            'admission.checklist_change_past_experiences': is_entity_manager
            & (general.in_sic_status | doctorate.in_sic_status)
            & ~is_sent_to_epc,
            'admission.checklist_select_access_title': is_entity_manager
            & (general.in_sic_status | doctorate.in_sic_status)
            & past_experiences_checklist_tab_is_not_sufficient
            & ~is_sent_to_epc,
            'admission.checklist_change_training_choice': is_entity_manager & doctorate.in_sic_status & ~is_sent_to_epc,
            'admission.checklist_change_sic_comment': is_entity_manager
            & (general.is_submitted | doctorate.is_submitted)
            & ~is_sent_to_epc,
            'admission.checklist_financability_dispensation': is_entity_manager & ~is_sent_to_epc,
            'admission.checklist_financability_dispensation_fac': is_entity_manager & ~is_sent_to_epc,
            'admission.continuing_checklist_change_iufc_comment': is_entity_manager & ~is_sent_to_epc,
            'admission.continuing_checklist_change_fac_comment': is_entity_manager & ~is_sent_to_epc,
            'admission.checklist_change_comment': is_entity_manager
            & (general.is_submitted | continuing.is_continuing | doctorate.is_submitted)
            & ~is_sent_to_epc,
            'admission.checklist_change_sic_decision': is_entity_manager
            & (general.in_sic_status | doctorate.in_sic_status)
            & ~is_sent_to_epc,
            'profil.can_see_parcours_externe': rules.always_allow,
            'profil.can_edit_parcours_externe': rules.always_allow,
            'admission.can_inject_to_epc': ~is_sent_to_epc,
            'admission.send_message': is_entity_manager,
            # Fusion
            'admission.merge_candidate_with_known_person': is_entity_manager & ~is_sent_to_epc,
        }
        return RuleSet(ruleset)
