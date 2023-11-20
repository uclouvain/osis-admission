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

from typing import List, Optional, Union

import attr

from admission.ddd.admission.doctorat.preparation.domain.model._institut import InstitutIdentity
from admission.ddd.admission.doctorat.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.admission.doctorat.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.admission.doctorat.preparation.domain.model._signature_promoteur import (
    SignaturePromoteur,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import InstitutTheseObligatoireException
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldPromoteurReferenceRenseignerInstitutThese(BusinessValidator):
    signatures_promoteurs: List[SignaturePromoteur]
    signataire: Union['PromoteurIdentity', 'MembreCAIdentity']
    promoteur_reference: Optional['PromoteurIdentity']
    proposition_institut_these: Optional[InstitutIdentity]
    institut_these: Optional[str]

    def validate(self, *args, **kwargs):
        if (
            isinstance(self.signataire, PromoteurIdentity)
            and self.signataire == self.promoteur_reference
            and not self.proposition_institut_these
            and not self.institut_these
        ):
            raise InstitutTheseObligatoireException()
