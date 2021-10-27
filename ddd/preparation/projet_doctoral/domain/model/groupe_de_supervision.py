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
import contextlib
from typing import List, Union

import attr

from admission.ddd.preparation.projet_doctoral.domain.model._cotutelle import Cotutelle, pas_de_cotutelle
from admission.ddd.preparation.projet_doctoral.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.preparation.projet_doctoral.domain.model._promoteur import PromoteurIdentity
from admission.ddd.preparation.projet_doctoral.domain.model._signature_membre_CA import SignatureMembreCA
from admission.ddd.preparation.projet_doctoral.domain.model._signature_promoteur import (
    ChoixEtatSignature,
    SignaturePromoteur,
)
from admission.ddd.preparation.projet_doctoral.domain.model.proposition import PropositionIdentity
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import SignataireNonTrouveException
from admission.ddd.preparation.projet_doctoral.domain.validator.validator_by_business_action import (
    ApprouverValidatorList,
    IdentifierMembreCAValidatorList,
    IdentifierPromoteurValidatorList,
    InviterASignerValidatorList,
    SupprimerMembreCAValidatorList,
    SupprimerPromoteurValidatorList,
)
from osis_common.ddd import interface


@attr.s(slots=True)
class GroupeDeSupervisionIdentity(interface.EntityIdentity):
    uuid = attr.ib(type=str)


@attr.s(slots=True)
class GroupeDeSupervision(interface.Entity):
    entity_id = attr.ib(type=GroupeDeSupervisionIdentity)
    proposition_id = attr.ib(type='PropositionIdentity')  # type: PropositionIdentity
    signatures_promoteurs = attr.ib(type=List[SignaturePromoteur], factory=list)  # type: List[SignaturePromoteur]
    signatures_membres_CA = attr.ib(type=List[SignatureMembreCA], factory=list)  # type: List[SignatureMembreCA]
    cotutelle = attr.ib(type=Cotutelle, default=pas_de_cotutelle)

    def identifier_promoteur(self, promoteur_id: 'PromoteurIdentity') -> None:
        IdentifierPromoteurValidatorList(
            groupe_de_supervision=self,
            promoteur_id=promoteur_id,
        ).validate()
        self.signatures_promoteurs.append(
            SignaturePromoteur(promoteur_id=promoteur_id, etat=ChoixEtatSignature.NOT_INVITED)
        )

    def identifier_membre_CA(self, membre_CA_id: 'MembreCAIdentity') -> None:
        IdentifierMembreCAValidatorList(
            groupe_de_supervision=self,
            membre_CA_id=membre_CA_id,
        ).validate()
        self.signatures_membres_CA.append(
            SignatureMembreCA(membre_CA_id=membre_CA_id, etat=ChoixEtatSignature.NOT_INVITED)
        )

    def get_signataire(self, matricule_signataire: str) -> Union['PromoteurIdentity', 'MembreCAIdentity']:
        with contextlib.suppress(StopIteration):
            return next(s.promoteur_id for s in self.signatures_promoteurs
                        if s.promoteur_id.matricule == matricule_signataire)
        with contextlib.suppress(StopIteration):
            return next(s.membre_CA_id for s in self.signatures_membres_CA
                        if s.membre_CA_id.matricule == matricule_signataire)
        raise SignataireNonTrouveException

    def inviter_a_signer(self, signataire_id: Union['PromoteurIdentity', 'MembreCAIdentity']) -> None:
        InviterASignerValidatorList(
            groupe_de_supervision=self,
            signataire_id=signataire_id,
        ).validate()
        if isinstance(signataire_id, PromoteurIdentity):
            self.signatures_promoteurs = [s for s in self.signatures_promoteurs if s.promoteur_id != signataire_id]
            self.signatures_promoteurs.append(
                SignaturePromoteur(promoteur_id=signataire_id, etat=ChoixEtatSignature.INVITED)
            )
        elif isinstance(signataire_id, MembreCAIdentity):
            self.signatures_membres_CA = [s for s in self.signatures_membres_CA if s.membre_CA_id != signataire_id]
            self.signatures_membres_CA.append(
                SignatureMembreCA(membre_CA_id=signataire_id, etat=ChoixEtatSignature.INVITED)
            )

    def supprimer_promoteur(self, promoteur_id: 'PromoteurIdentity') -> None:
        SupprimerPromoteurValidatorList(
            groupe_de_supervision=self,
            promoteur_id=promoteur_id,
        ).validate()
        self.signatures_promoteurs = [s for s in self.signatures_promoteurs if s.promoteur_id != promoteur_id]

    def supprimer_membre_CA(self, membre_CA_id: 'MembreCAIdentity') -> None:
        SupprimerMembreCAValidatorList(
            groupe_de_supervision=self,
            membre_CA_id=membre_CA_id,
        ).validate()
        self.signatures_membres_CA = [s for s in self.signatures_membres_CA if s.membre_CA_id != membre_CA_id]

    def approuver(self, signataire_id: Union['PromoteurIdentity', 'MembreCAIdentity']) -> None:
        ApprouverValidatorList(
            groupe_de_supervision=self,
            signataire_id=signataire_id,
        ).validate()
        if isinstance(signataire_id, PromoteurIdentity):
            self.signatures_promoteurs = [s for s in self.signatures_promoteurs if s.promoteur_id != signataire_id]
            self.signatures_promoteurs.append(
                SignaturePromoteur(promoteur_id=signataire_id, etat=ChoixEtatSignature.APPROVED)
            )
        elif isinstance(signataire_id, MembreCAIdentity):
            self.signatures_membres_CA = [s for s in self.signatures_membres_CA if s.membre_CA_id != signataire_id]
            self.signatures_membres_CA.append(
                SignatureMembreCA(membre_CA_id=signataire_id, etat=ChoixEtatSignature.APPROVED)
            )

    def verifier_tout_le_monde_a_approuve(self):
        raise NotImplementedError

    def verifier_cotutelle(self):
        raise NotImplementedError

    def definir_cotutelle(self,
                          motivation: str,
                          institution: str,
                          demande_ouverture: List[str] = None,
                          convention: List[str] = None,
                          autres_documents: List[str] = None,
                          ):
        self.cotutelle = Cotutelle(
            motivation=motivation,
            institution=institution,
            demande_ouverture=demande_ouverture,
            convention=convention,
            autres_documents=autres_documents,
        )
