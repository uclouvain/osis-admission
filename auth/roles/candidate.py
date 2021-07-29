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
from rules import RuleSet
from django.utils.translation import gettext_lazy as _

from admission.auth.predicates import is_admission_request_author
from osis_role.contrib.models import EntityRoleModel


class Candidate(EntityRoleModel):
    class Meta:
        verbose_name = _("Candidate")
        verbose_name_plural = _("Candidates")
        group_name = "candidates"

    @classmethod
    def rule_set(cls):
        return RuleSet({
            'admission.add_doctorateadmission': rules.always_allow,
            'admission.change_doctorateadmission': is_admission_request_author,
            'admission.view_doctorateadmission': is_admission_request_author,
            'admission.delete_doctorateadmission': rules.always_deny,
            'admission.access_doctorateadmission': rules.always_allow,
            'admission.download_pdf_confirmation': is_admission_request_author,
            'admission.upload_pdf_confirmation': is_admission_request_author,
            'admission.fill_thesis': is_admission_request_author,
            'admission.upload_publication_authorisation': is_admission_request_author,
        })
