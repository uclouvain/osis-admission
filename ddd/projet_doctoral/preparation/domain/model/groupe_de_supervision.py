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
from typing import List, Optional, Union

import attr

from admission.ddd.projet_doctoral.preparation.domain.model._cotutelle import Cotutelle
from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixStatutSignatureGroupeDeSupervision
from admission.ddd.projet_doctoral.preparation.domain.model._institut import InstitutIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._signature_membre_CA import SignatureMembreCA
from admission.ddd.projet_doctoral.preparation.domain.model._signature_promoteur import (
    ChoixEtatSignature,
    SignaturePromoteur,
)
from admission.ddd.projet_doctoral.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.projet_doctoral.preparation.domain.validator.exceptions import (
    MembreCANonTrouveException,
    PromoteurNonTrouveException,
    SignataireNonTrouveException,
)
from admission.ddd.projet_doctoral.preparation.domain.validator.validator_by_business_action import (
    ApprobationPromoteurValidatorList,
    ApprobationValidatorList,
    ApprouverValidatorList,
    CotutelleValidatorList,
    IdentifierMembreCAValidatorList,
    IdentifierPromoteurValidatorList,
    InviterASignerValidatorList,
    SignatairesValidatorList,
    SupprimerMembreCAValidatorList,
    SupprimerPromoteurValidatorList,
)
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class GroupeDeSupervisionIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True)
class GroupeDeSupervision(interface.RootEntity):
    entity_id: 'GroupeDeSupervisionIdentity'
    proposition_id: 'PropositionIdentity'
    signatures_promoteurs: List['SignaturePromoteur'] = attr.Factory(list)
    signatures_membres_CA: List['SignatureMembreCA'] = attr.Factory(list)
    cotutelle: Optional['Cotutelle'] = None
    statut_signature: ChoixStatutSignatureGroupeDeSupervision = ChoixStatutSignatureGroupeDeSupervision.IN_PROGRESS

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
            return next(
                s.promoteur_id for s in self.signatures_promoteurs if s.promoteur_id.matricule == matricule_signataire
            )
        with contextlib.suppress(StopIteration):
            return next(
                s.membre_CA_id for s in self.signatures_membres_CA if s.membre_CA_id.matricule == matricule_signataire
            )
        raise SignataireNonTrouveException

    def get_promoteur(self, matricule_signataire: str) -> 'PromoteurIdentity':
        promoteur = self.get_signataire(matricule_signataire)
        if not isinstance(promoteur, PromoteurIdentity):
            raise PromoteurNonTrouveException
        return promoteur

    def get_membre_CA(self, matricule_signataire: str) -> 'MembreCAIdentity':
        membre_CA = self.get_signataire(matricule_signataire)
        if not isinstance(membre_CA, MembreCAIdentity):
            raise MembreCANonTrouveException
        return membre_CA

    def inviter_a_signer(self) -> None:
        """Inviter à signer tous les promoteurs et membres CA non invités ou refusés"""
        etats_initiaux = [ChoixEtatSignature.NOT_INVITED, ChoixEtatSignature.DECLINED]
        for promoteur in filter(lambda s: s.etat in etats_initiaux, self.signatures_promoteurs):
            InviterASignerValidatorList(groupe_de_supervision=self, signataire_id=promoteur.promoteur_id).validate()
            self.signatures_promoteurs = [s for s in self.signatures_promoteurs if s != promoteur]
            self.signatures_promoteurs.append(
                SignaturePromoteur(promoteur_id=promoteur.promoteur_id, etat=ChoixEtatSignature.INVITED)
            )
        for membre_CA in filter(lambda s: s.etat in etats_initiaux, self.signatures_membres_CA):
            InviterASignerValidatorList(groupe_de_supervision=self, signataire_id=membre_CA.membre_CA_id).validate()
            self.signatures_membres_CA = [s for s in self.signatures_membres_CA if s != membre_CA]
            self.signatures_membres_CA.append(
                SignatureMembreCA(membre_CA_id=membre_CA.membre_CA_id, etat=ChoixEtatSignature.INVITED)
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

    def approuver(
        self,
        signataire_id: Union['PromoteurIdentity', 'MembreCAIdentity'],
        commentaire_interne: Optional[str],
        commentaire_externe: Optional[str],
    ) -> None:
        ApprouverValidatorList(
            groupe_de_supervision=self,
            signataire_id=signataire_id,
        ).validate()
        if isinstance(signataire_id, PromoteurIdentity):
            self.signatures_promoteurs = [s for s in self.signatures_promoteurs if s.promoteur_id != signataire_id]
            self.signatures_promoteurs.append(
                SignaturePromoteur(
                    promoteur_id=signataire_id,
                    etat=ChoixEtatSignature.APPROVED,
                    commentaire_interne=commentaire_interne or '',
                    commentaire_externe=commentaire_externe or '',
                )
            )
        elif isinstance(signataire_id, MembreCAIdentity):  # pragma: no branch
            self.signatures_membres_CA = [s for s in self.signatures_membres_CA if s.membre_CA_id != signataire_id]
            self.signatures_membres_CA.append(
                SignatureMembreCA(
                    membre_CA_id=signataire_id,
                    etat=ChoixEtatSignature.APPROVED,
                    commentaire_interne=commentaire_interne or '',
                    commentaire_externe=commentaire_externe or '',
                )
            )

    def approuver_par_pdf(
        self,
        signataire_id: Union['PromoteurIdentity', 'MembreCAIdentity'],
        pdf: List[str],
    ) -> None:
        ApprouverValidatorList(
            groupe_de_supervision=self,
            signataire_id=signataire_id,
        ).validate()
        if isinstance(signataire_id, PromoteurIdentity):
            self.signatures_promoteurs = [s for s in self.signatures_promoteurs if s.promoteur_id != signataire_id]
            self.signatures_promoteurs.append(
                SignaturePromoteur(
                    promoteur_id=signataire_id,
                    etat=ChoixEtatSignature.APPROVED,
                    pdf=pdf,
                )
            )
        elif isinstance(signataire_id, MembreCAIdentity):  # pragma: no branch
            self.signatures_membres_CA = [s for s in self.signatures_membres_CA if s.membre_CA_id != signataire_id]
            self.signatures_membres_CA.append(
                SignatureMembreCA(
                    membre_CA_id=signataire_id,
                    etat=ChoixEtatSignature.APPROVED,
                    pdf=pdf,
                )
            )

    def refuser(
        self,
        signataire_id: Union['PromoteurIdentity', 'MembreCAIdentity'],
        commentaire_interne: Optional[str],
        commentaire_externe: Optional[str],
        motif_refus: Optional[str],
    ) -> None:
        ApprouverValidatorList(
            groupe_de_supervision=self,
            signataire_id=signataire_id,
        ).validate()
        if isinstance(signataire_id, PromoteurIdentity):
            # Add signature state for promoter refusing and reset all others signatures
            new_states = []
            for s in self.signatures_promoteurs:
                if s.promoteur_id != signataire_id:
                    # Reset all others signatures
                    new_states.append(attr.evolve(s, etat=ChoixEtatSignature.NOT_INVITED))
                else:
                    # Add signature state for promoter refusing
                    new_states.append(
                        SignaturePromoteur(
                            promoteur_id=signataire_id,
                            etat=ChoixEtatSignature.DECLINED,
                            commentaire_interne=commentaire_interne or '',
                            commentaire_externe=commentaire_externe or '',
                            motif_refus=motif_refus or '',
                        )
                    )
            self.signatures_promoteurs = new_states
        else:
            # Simply remove the CA member
            self.signatures_membres_CA = [s for s in self.signatures_membres_CA if s.membre_CA_id != signataire_id]

    def verifier_tout_le_monde_a_approuve(self):
        ApprobationValidatorList(groupe_de_supervision=self).validate()

    def verifier_cotutelle(self):
        CotutelleValidatorList(cotutelle=self.cotutelle).validate()

    def definir_cotutelle(
        self,
        motivation: Optional[str],
        institution_fwb: Optional[bool],
        institution: Optional[str],
        demande_ouverture: List[str] = None,
        convention: List[str] = None,
        autres_documents: List[str] = None,
    ):
        self.cotutelle = Cotutelle(
            motivation=motivation or '',
            institution_fwb=institution_fwb,
            institution=institution or '',
            demande_ouverture=demande_ouverture or [],
            convention=convention or [],
            autres_documents=autres_documents or [],
        )

    def verrouiller_groupe_pour_signature(self):
        self.statut_signature = ChoixStatutSignatureGroupeDeSupervision.SIGNING_IN_PROGRESS

    def verifier_signataires(self):
        SignatairesValidatorList(groupe_de_supervision=self).validate()

    def verifier_premier_promoteur_renseigne_institut_these(
        self,
        signataire: Union[PromoteurIdentity, MembreCAIdentity],
        proposition_institut_these: Optional[InstitutIdentity],
        institut_these: Optional[str],
    ):
        ApprobationPromoteurValidatorList(
            signatures_promoteurs=self.signatures_promoteurs,
            signataire=signataire,
            proposition_institut_these=proposition_institut_these,
            institut_these=institut_these,
        ).validate()
