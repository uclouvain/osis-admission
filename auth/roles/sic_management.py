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
from rules import RuleSet

from admission.auth.predicates.common import is_entity_manager, is_sent_to_epc
from admission.auth.roles.central_manager import CentralManager
from base.auth.roles.sic_management import SicManagement


class AdmissionSicManagement(SicManagement):
    """
    Direction SIC

    L'assistant à la direction SIC intervient dans l'admission pour valider l'autorisation d'inscription.
    Il a un peu plus de pouvoir que le gestionnaire central d'admission.
    """

    class Meta:
        group_name = "sic_management"
        proxy = True

    @classmethod
    def rule_set(cls):
        ruleset = {
            **CentralManager.rule_set_without_scope(),
            # Listings
            'admission.checklist_change_sic_decision': rules.always_allow & ~is_sent_to_epc,
            'admission.view_enrolment_applications': rules.always_allow,
            'admission.view_doctorate_enrolment_applications': rules.always_allow,
            'admission.view_continuing_enrolment_applications': rules.always_allow,
            'admission.validate_registration': is_entity_manager,
            # Fusion
            'admission.merge_candidate_with_known_person': is_entity_manager & ~is_sent_to_epc,
        }
        return RuleSet(ruleset)
