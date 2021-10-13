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
import attr

from base.ddd.utils.business_validator import BusinessValidator
from admission.ddd.preparation.projet_doctoral.business_types import *
from admission.ddd.preparation.projet_doctoral.domain.model._signature_promoteur import ChoixEtatSignature
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (
    SignataireDejaInviteException,
)


@attr.s(frozen=True, slots=True)
class ShouldSignatairePasDejaInvite(BusinessValidator):
    groupe_de_supervision = attr.ib(type='GroupeDeSupervision')  # type: GroupeDeSupervision
    signataire_id = attr.ib(type="Union['PromoteurIdentity', 'MembreCAIdentity']")  # type: Union['PromoteurIdentity', 'MembreCAIdentity']

    def validate(self, *args, **kwargs):
        if (
                any(s for s in self.groupe_de_supervision.signatures_promoteurs
                    if s.promoteur_id == self.signataire_id and s.etat != ChoixEtatSignature.NOT_INVITED)
                or any(s for s in self.groupe_de_supervision.signatures_membres_CA
                       if s.membre_CA_id == self.signataire_id and s.etat != ChoixEtatSignature.NOT_INVITED)
        ):
            raise SignataireDejaInviteException
