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
import rules
from django.db import models

from admission.auth.predicates import is_part_of_education_group, is_debug
from base.models.education_group import EducationGroup
from education_group.contrib.models import EducationGroupRoleModel
from django.utils.translation import gettext_lazy as _


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
            # TODO check which education group is linked?
            'admission.view_doctorate_enrolment_applications': rules.always_allow,
            'admission.view_continuing_enrolment_applications': rules.always_allow,
            # Access a single application
            'admission.view_enrolment_application': is_part_of_education_group,
            # Profile
            'admission.view_doctorateadmission_person': is_part_of_education_group,
            'admission.change_doctorateadmission_person': is_part_of_education_group,
            'admission.view_doctorateadmission_coordinates': is_part_of_education_group,
            'admission.change_doctorateadmission_coordinates': is_part_of_education_group,
            'admission.view_doctorateadmission_secondary_studies': is_part_of_education_group,
            'admission.change_doctorateadmission_secondary_studies': is_part_of_education_group,
            'admission.view_doctorateadmission_languages': is_part_of_education_group,
            'admission.change_doctorateadmission_languages': is_part_of_education_group,
            'admission.view_doctorateadmission_curriculum': is_part_of_education_group,
            'admission.change_doctorateadmission_curriculum': is_part_of_education_group,
            # Project
            'admission.view_doctorateadmission_project': is_part_of_education_group,
            'admission.change_doctorateadmission_project': is_part_of_education_group,
            'admission.view_doctorateadmission_cotutelle': is_part_of_education_group,
            'admission.change_doctorateadmission_cotutelle': is_part_of_education_group,
            # Supervision
            'admission.view_doctorateadmission_supervision': is_part_of_education_group,
            'admission.change_doctorateadmission_supervision': is_part_of_education_group,
            'admission.add_supervision_member': is_part_of_education_group,
            'admission.remove_supervision_member': is_part_of_education_group,
            'admission.view_historyentry': is_part_of_education_group,
            # Management
            'admission.add_internalnote': is_part_of_education_group,
            'admission.view_internalnote': is_part_of_education_group,
            'admission.view_debug_info': is_part_of_education_group & is_debug,
            # Exports
            'admission.download_doctorateadmission_pdf_recap': is_part_of_education_group,
        }
        return rules.RuleSet(ruleset)
