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
from typing import TYPE_CHECKING, Union

import attr

from admission.ddd.projet_doctoral.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._signature_promoteur import ChoixEtatSignature
from admission.ddd.projet_doctoral.preparation.domain.validator.exceptions import SignatairePasInviteException
from base.ddd.utils.business_validator import BusinessValidator

if TYPE_CHECKING:
    from admission.ddd.projet_doctoral.preparation.domain.model.groupe_de_supervision import GroupeDeSupervision


@attr.dataclass(frozen=True, slots=True)
class ShouldSignataireEtreInvite(BusinessValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    signataire_id: Union['PromoteurIdentity', 'MembreCAIdentity']

    def validate(self, *args, **kwargs):
        if not any(
            signature
            for signature in self.groupe_de_supervision.signatures_promoteurs
            if signature.promoteur_id == self.signataire_id and signature.etat == ChoixEtatSignature.INVITED
        ) and not any(
            signature
            for signature in self.groupe_de_supervision.signatures_membres_CA
            if signature.membre_CA_id == self.signataire_id and signature.etat == ChoixEtatSignature.INVITED
        ):
            raise SignatairePasInviteException
