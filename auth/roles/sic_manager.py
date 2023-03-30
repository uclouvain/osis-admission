# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import rules
from django.utils.translation import gettext_lazy as _
from rules import RuleSet

from admission.auth.predicates import is_debug
from osis_role.contrib.models import RoleModel


class SicManager(RoleModel):
    class Meta:
        verbose_name = _("Role: SIC manager")
        verbose_name_plural = _("Role: SIC managers")
        group_name = "sic_managers"

    @classmethod
    def rule_set(cls):
        ruleset = {
            # Common
            # > Listing
            'admission.view_dossiers': rules.always_allow,
            # > Management
            'admission.view_internalnote': rules.always_allow,
            'admission.view_debug_info': is_debug,
            # Doctorate
            'admission.change_doctorateadmission': rules.always_allow,
            'admission.delete_doctorateadmission': rules.always_deny,
            'admission.view_doctorateadmission': rules.always_allow,
            'admission.appose_sic_notice': rules.always_allow,
            'admission.view_doctorateadmission_person': rules.always_allow,
            'admission.change_doctorateadmission_person': rules.always_allow,
            'admission.view_doctorateadmission_coordinates': rules.always_allow,
            'admission.change_doctorateadmission_coordinates': rules.always_allow,
            'admission.view_doctorateadmission_secondary_studies': rules.always_allow,
            'admission.change_doctorateadmission_secondary_studies': rules.always_allow,
            'admission.view_doctorateadmission_curriculum': rules.always_allow,
            'admission.change_doctorateadmission_curriculum': rules.always_allow,
            'admission.view_doctorateadmission_project': rules.always_allow,
            'admission.change_doctorateadmission_project': rules.always_allow,
            'admission.view_doctorateadmission_cotutelle': rules.always_allow,
            'admission.change_doctorateadmission_cotutelle': rules.always_allow,
            'admission.view_doctorateadmission_supervision': rules.always_allow,
            'admission.add_supervision_member': rules.always_allow,
            'admission.remove_supervision_member': rules.always_allow,
            # General admission
            'admission.view_generaleducationadmission': rules.always_allow,
            'admission.view_generaleducationadmission_person': rules.always_allow,
            'admission.change_generaleducationadmission_person': rules.always_allow,
            'admission.view_generaleducationadmission_coordinates': rules.always_allow,
            'admission.change_generaleducationadmission_coordinates': rules.always_allow,
            'admission.view_generaleducationadmission_curriculum': rules.always_allow,
            'admission.view_generaleducationadmission_secondary_studies': rules.always_allow,
            'admission.view_generaleducationadmission_languages': rules.always_allow,
            'admission.view_generaleducationadmission_accounting': rules.always_allow,
            'admission.view_generaleducationadmission_specific_question': rules.always_allow,
            'admission.download_generaleducationadmission_pdf_recap': rules.always_allow,
            # Continuing admission
            'admission.view_continuingeducationadmission': rules.always_allow,
            'admission.view_continuingeducationadmission_person': rules.always_allow,
            'admission.change_continuingeducationadmission_person': rules.always_allow,
            'admission.view_continuingeducationadmission_coordinates': rules.always_allow,
            'admission.change_continuingeducationadmission_coordinates': rules.always_allow,
            'admission.view_continuingeducationadmission_curriculum': rules.always_allow,
            'admission.view_continuingeducationadmission_secondary_studies': rules.always_allow,
            'admission.view_continuingeducationadmission_languages': rules.always_allow,
            'admission.view_continuingeducationadmission_specific_question': rules.always_allow,
            'admission.download_continuingeducationadmission_pdf_recap': rules.always_allow,
        }
        return RuleSet(ruleset)
