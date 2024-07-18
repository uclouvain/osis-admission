###############################################################################
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
from rules import RuleSet

from admission.auth.predicates.common import has_education_group_of_types, is_part_of_education_group
from admission.auth.predicates import general, continuing, doctorate
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from parcours_interne.auth.roles.parcours_viewer import ParcoursViewer


class AdmissionReader(ParcoursViewer):
    class Meta:
        group_name = "parcours_viewers"
        proxy = True

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
            'admission.view_doctorateadmission': is_part_of_education_group,
            # Profile
            'admission.view_admission_person': is_part_of_education_group,
            'admission.view_admission_coordinates': is_part_of_education_group,
            'admission.view_admission_secondary_studies': is_part_of_education_group,
            'admission.view_admission_languages': is_part_of_education_group,
            'admission.view_admission_curriculum': is_part_of_education_group,
            # Project
            'admission.view_admission_project': is_part_of_education_group,
            'admission.view_admission_cotutelle': is_part_of_education_group,
            'admission.view_admission_training_choice': is_part_of_education_group,
            'admission.view_admission_accounting': is_part_of_education_group,
            'admission.view_admission_specific_questions': is_part_of_education_group,
            # Supervision
            'admission.view_admission_supervision': is_part_of_education_group,
            'admission.view_historyentry': is_part_of_education_group,
            # Management
            'admission.view_documents_management': is_part_of_education_group
            & (general.is_submitted | continuing.is_submitted | doctorate.is_submitted),
            'admission.view_checklist': is_part_of_education_group
            & (general.is_submitted | continuing.is_submitted | doctorate.is_submitted),
        }
        return RuleSet(ruleset)
