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
from typing import List

import attr

from admission.ddd.preparation.projet_doctoral.domain.model._enums import ChoixStatutSignatureGroupeDeSupervision
from admission.ddd.preparation.projet_doctoral.domain.model._signature_membre_CA import SignatureMembreCA
from admission.ddd.preparation.projet_doctoral.domain.model._signature_promoteur import (
    ChoixEtatSignature,
    SignaturePromoteur,
)
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (
    ProcedureDemandeSignatureNonLanceeException,
    PropositionNonApprouveeParPromoteurException,
    PropositionNonApprouveeParMembresCAException,
)
from base.ddd.utils.business_validator import BusinessValidator


@attr.s(frozen=True, slots=True)
class ShouldDemandeSignatureLancee(BusinessValidator):
    statut_signature = attr.ib(type=ChoixStatutSignatureGroupeDeSupervision)

    def validate(self, *args, **kwargs):
        if self.statut_signature != ChoixStatutSignatureGroupeDeSupervision.SIGNING_IN_PROGRESS:
            raise ProcedureDemandeSignatureNonLanceeException


@attr.s(frozen=True, slots=True)
class ShouldPromoteursOntApprouve(BusinessValidator):
    signatures_promoteurs = attr.ib(type=List[SignaturePromoteur])  # type: List[SignaturePromoteur]

    def validate(self, *args, **kwargs):
        if any(signature.etat != ChoixEtatSignature.APPROVED for signature in self.signatures_promoteurs):
            raise PropositionNonApprouveeParPromoteurException


@attr.s(frozen=True, slots=True)
class ShouldMembresCAOntApprouve(BusinessValidator):
    signatures_membres_CA = attr.ib(type=List[SignatureMembreCA])  # type: List[SignatureMembreCA]

    def validate(self, *args, **kwargs):
        if any(signature.etat != ChoixEtatSignature.APPROVED for signature in self.signatures_membres_CA):
            raise PropositionNonApprouveeParMembresCAException
