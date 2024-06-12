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
from django.db import models
from django.utils.translation import gettext_lazy as _

from admission.auth.predicates.common import (
    has_education_group_of_types,
    is_part_of_education_group,
    is_debug,
)
from admission.auth.predicates import general, continuing
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
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
            'admission.view_enrolment_applications': rules.always_allow,
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
            'admission.change_admission_person': is_part_of_education_group & continuing.in_manager_status,
            'admission.view_admission_coordinates': is_part_of_education_group,
            'admission.change_admission_coordinates': is_part_of_education_group & continuing.in_manager_status,
            'admission.view_admission_secondary_studies': is_part_of_education_group,
            'admission.view_admission_languages': is_part_of_education_group,
            'admission.view_admission_curriculum': is_part_of_education_group,
            # Project
            'admission.view_admission_project': is_part_of_education_group,
            'admission.view_admission_cotutelle': is_part_of_education_group,
            'admission.view_admission_training_choice': is_part_of_education_group,
            'admission.change_admission_training_choice': is_part_of_education_group & continuing.in_manager_status,
            'admission.view_admission_accounting': is_part_of_education_group,
            'admission.view_admission_specific_questions': is_part_of_education_group,
            'admission.change_admission_specific_questions': is_part_of_education_group & continuing.in_manager_status,
            # Supervision
            'admission.view_admission_supervision': is_part_of_education_group,
            'admission.change_admission_supervision': is_part_of_education_group,
            'admission.add_supervision_member': is_part_of_education_group,
            'admission.remove_supervision_member': is_part_of_education_group,
            'admission.view_historyentry': is_part_of_education_group,
            # Management
            'admission.add_internalnote': is_part_of_education_group,
            'admission.view_internalnote': is_part_of_education_group,
            'admission.view_documents_management': is_part_of_education_group
            & ((general.is_general & general.is_submitted) | (continuing.is_continuing & continuing.not_cancelled)),
            'admission.edit_documents': is_part_of_education_group
            & ((general.is_general & general.is_submitted) | (continuing.is_continuing & continuing.not_cancelled)),
            'admission.request_documents': is_part_of_education_group
            & (
                (general.is_general & general.in_fac_status)
                | (continuing.is_continuing & continuing.can_request_documents)
            ),
            'admission.cancel_document_request': is_part_of_education_group
            & (
                (general.is_general & general.in_fac_document_request_status)
                | (continuing.is_continuing & continuing.in_document_request_status)
            ),
            'admission.generate_in_progress_analysis_folder': is_part_of_education_group
            & continuing.is_continuing
            & continuing.in_progress,
            'admission.view_checklist': is_part_of_education_group & (general.is_submitted | continuing.is_submitted),
            'admission.change_checklist': is_part_of_education_group
            & continuing.is_continuing
            & continuing.is_submitted,
            'admission.checklist_change_faculty_decision': is_part_of_education_group & general.in_fac_status,
            'admission.checklist_faculty_decision_transfer_to_sic_with_decision': is_part_of_education_group
            & general.in_fac_status,
            'admission.checklist_faculty_decision_transfer_to_sic_without_decision': is_part_of_education_group
            & general.in_fac_status,
            'admission.checklist_select_access_title': is_part_of_education_group & general.in_fac_status,
            'admission.checklist_change_fac_comment': is_part_of_education_group,
            'admission.continuing_checklist_change_fac_comment': is_part_of_education_group,
            'admission.checklist_change_comment': is_part_of_education_group & continuing.is_continuing,
            'admission.view_debug_info': is_part_of_education_group & is_debug,
            # Exports
            'admission.download_doctorateadmission_pdf_recap': is_part_of_education_group,
        }
        return rules.RuleSet(ruleset)
