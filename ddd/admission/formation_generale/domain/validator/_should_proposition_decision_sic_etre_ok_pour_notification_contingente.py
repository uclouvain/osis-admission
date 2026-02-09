# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional

import attr

from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    AdmissionContingenteNotificationStatusDecisionSicInvalideException,
)
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldPropositionDecisionSicEtreOkPourNotificationContingente(BusinessValidator):
    decision_sic: 'StatutChecklist'

    def validate(self, *args, **kwargs):
        if not (
            self.decision_sic.statut == ChoixStatutChecklist.INITIAL_CANDIDAT
            or (
                self.decision_sic.statut == ChoixStatutChecklist.GEST_BLOCAGE
                and self.decision_sic.extra.get('blocage') == 'to_be_completed'
            )
            or (
                self.decision_sic.statut == ChoixStatutChecklist.GEST_EN_COURS
                and self.decision_sic.extra.get('en_cours') == 'derogation'
            )
            or (
                self.decision_sic.statut == ChoixStatutChecklist.GEST_EN_COURS
                and self.decision_sic.extra.get('en_cours') == 'approval'
            )
        ):
            raise AdmissionContingenteNotificationStatusDecisionSicInvalideException()
