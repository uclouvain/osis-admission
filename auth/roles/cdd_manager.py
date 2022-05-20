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

from admission.auth.predicates import is_enrolled, is_part_of_doctoral_commission
from osis_role.contrib.models import EntityRoleModel


class CddManager(EntityRoleModel):
    class Meta:
        verbose_name = _("CDD manager")
        verbose_name_plural = _("CDD managers")
        group_name = "cdd_managers"

    @classmethod
    def rule_set(cls):
        ruleset = {
            'admission.change_doctorateadmission': is_part_of_doctoral_commission,
            'admission.view_doctorateadmission': is_part_of_doctoral_commission,
            'admission.delete_doctorateadmission': rules.always_deny,
            'admission.appose_cdd_notice': is_part_of_doctoral_commission,
            'admission.download_pdf_confirmation': is_part_of_doctoral_commission,
            'admission.upload_pdf_confirmation': rules.always_deny,
            'admission.approve_confirmation_paper': is_part_of_doctoral_commission,
            'admission.validate_doctoral_training': is_part_of_doctoral_commission,
            'admission.fill_thesis': is_part_of_doctoral_commission,
            'admission.submit_thesis': is_part_of_doctoral_commission,
            'admission.upload_defense_report': is_part_of_doctoral_commission,
            'admission.view_doctorateadmission_person': is_part_of_doctoral_commission,
            'admission.change_doctorateadmission_person': is_part_of_doctoral_commission,
            'admission.view_doctorateadmission_coordinates': is_part_of_doctoral_commission,
            'admission.change_doctorateadmission_coordinates': is_part_of_doctoral_commission,
            'admission.view_doctorateadmission_secondary_studies': is_part_of_doctoral_commission,
            'admission.change_doctorateadmission_secondary_studies': is_part_of_doctoral_commission,
            'admission.view_doctorateadmission_languages': is_part_of_doctoral_commission,
            'admission.change_doctorateadmission_languages': is_part_of_doctoral_commission,
            'admission.view_doctorateadmission_curriculum': is_part_of_doctoral_commission,
            'admission.change_doctorateadmission_curriculum': is_part_of_doctoral_commission,
            'admission.view_doctorateadmission_project': is_part_of_doctoral_commission,
            'admission.change_doctorateadmission_project': is_part_of_doctoral_commission,
            'admission.view_doctorateadmission_cotutelle': is_part_of_doctoral_commission,
            'admission.change_doctorateadmission_cotutelle': is_part_of_doctoral_commission,
            'admission.view_doctorateadmission_supervision': is_part_of_doctoral_commission,
            'admission.change_doctorateadmission_supervision': is_part_of_doctoral_commission,
            'admission.view_doctorateadmission_confirmation': is_part_of_doctoral_commission,
            'admission.change_doctorateadmission_confirmation': is_part_of_doctoral_commission,
            'admission.add_supervision_member': is_part_of_doctoral_commission,
            'admission.remove_supervision_member': is_part_of_doctoral_commission,
            'admission.change_cddmailtemplate': rules.always_allow,
            'admission.view_cdddossiers': rules.always_allow,
            'osis_history.view_historyentry': is_part_of_doctoral_commission,
            'admission.send_message': is_part_of_doctoral_commission & is_enrolled,
        }
        return RuleSet(ruleset)
