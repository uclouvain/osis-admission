# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Optional

import attr

from admission.ddd.admission.enums import ChoixAffiliationSport
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AffiliationsNonCompleteesException,
    ReductionDesDroitsInscriptionNonCompleteeException,
)
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldReductionDesDroitsInscriptionEtreCompletee(BusinessValidator):
    demande_allocation_d_etudes_communaute_francaise_belgique: Optional[bool]
    enfant_personnel: Optional[bool]

    def validate(self, *args, **kwargs):
        if self.demande_allocation_d_etudes_communaute_francaise_belgique is None or self.enfant_personnel is None:
            raise ReductionDesDroitsInscriptionNonCompleteeException


@attr.dataclass(frozen=True, slots=True)
class ShouldAffiliationsEtreCompletees(BusinessValidator):
    affiliation_sport: Optional[ChoixAffiliationSport]
    etudiant_solidaire: Optional[bool]

    def validate(self, *args, **kwargs):
        if not self.affiliation_sport or self.etudiant_solidaire is None:
            raise AffiliationsNonCompleteesException
