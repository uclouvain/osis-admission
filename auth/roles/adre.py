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
from rules import RuleSet

from admission.auth.predicates import is_enrolled
from osis_role.contrib.models import RoleModel
from django.utils.translation import gettext_lazy as _


class AdreSecretary(RoleModel):
    """
    Secrétaire ADRE

    Intervient pour télécharger/-verser des documents (ex : demande de renouvellement de bourse lors de la confirmation)
    et pour vérifier la pertinence de la publication de la thèse.
    """

    class Meta:
        verbose_name = _("Role: ADRE secretary")
        verbose_name_plural = _("Role: ADRE Secretaries")
        group_name = "adre_secretary"

    @classmethod
    def rule_set(cls):
        ruleset = {
            # Doctorate
            'admission.view_doctorateadmission': rules.always_allow,
            'admission.download_jury_approved_pdf': rules.always_allow,
            'admission.upload_jury_approved_pdf': rules.always_allow,
            'admission.upload_signed_scholarship': rules.always_allow,
            'admission.check_publication_authorisation': rules.always_allow,
            'admission.view_doctorate_enrolment_applications': rules.always_allow,
            'admission.view_enrolment_applications': rules.always_allow,
            'admission.view_admission_person': rules.always_allow,
            'admission.view_admission_coordinates': rules.always_allow,
            'admission.view_admission_secondary_studies': rules.always_allow,
            'admission.view_admission_curriculum': rules.always_allow,
            'admission.view_admission_project': rules.always_allow,
            'admission.view_admission_cotutelle': rules.always_allow,
            'admission.view_admission_supervision': rules.always_allow,
            'admission.view_admission_languages': rules.always_allow,
            'admission.view_admission_confirmation': rules.always_allow & is_enrolled,
            'admission.upload_pdf_confirmation': rules.always_allow & is_enrolled,
            'admission.view_historyentry': rules.always_allow,
            'admission.send_message': rules.always_allow & is_enrolled,
            'admission.view_internalnote': rules.always_allow,
        }
        return RuleSet(ruleset)
