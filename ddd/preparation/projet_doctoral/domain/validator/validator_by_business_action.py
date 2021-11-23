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
from typing import Optional, List, Union

import attr

from admission.ddd.preparation.projet_doctoral.business_types import *
from admission.ddd.preparation.projet_doctoral.domain.model._cotutelle import Cotutelle
from admission.ddd.preparation.projet_doctoral.domain.model._detail_projet import DetailProjet
from admission.ddd.preparation.projet_doctoral.domain.model._enums import ChoixTypeAdmission
from admission.ddd.preparation.projet_doctoral.domain.model._experience_precedente_recherche import (
    ChoixDoctoratDejaRealise,
)
from admission.ddd.preparation.projet_doctoral.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.preparation.projet_doctoral.domain.model._promoteur import PromoteurIdentity
from admission.ddd.preparation.projet_doctoral.domain.validator import (
    ShouldInstitutionDependreDoctoratRealise,
    ShouldJustificationDonneeSiPreadmission,
    ShouldMembreCAEtreDansGroupeDeSupervision,
    ShouldMembreCAPasDejaPresentDansGroupeDeSupervision,
    ShouldPromoteurEtreDansGroupeDeSupervision,
    ShouldPromoteurPasDejaPresentDansGroupeDeSupervision,
    ShouldSignataireEtreDansGroupeDeSupervision,
    ShouldSignataireEtreInvite,
    ShouldSignatairePasDejaInvite,
    ShouldTypeContratTravailDependreTypeFinancement,
)
from admission.ddd.preparation.projet_doctoral.domain.validator._should_cotutelle_etre_completee import (
    ShouldCotutelleEtreComplete,
)
from admission.ddd.preparation.projet_doctoral.domain.validator._should_detail_projet_etre_complete import (
    ShouldDetailProjetEtreComplete,
)
from admission.ddd.preparation.projet_doctoral.domain.validator.\
    _should_groupe_de_supervision_avoir_au_moins_un_membre_CA import ShouldGroupeDeSupervisionAvoirAuMoinsUnMembreCA
from admission.ddd.preparation.projet_doctoral.domain.validator.\
    _should_groupe_de_supervision_avoir_au_moins_un_promoteur import ShouldGroupeDeSupervisionAvoirAuMoinsUnPromoteur
from base.ddd.utils.business_validator import TwoStepsMultipleBusinessExceptionListValidator, BusinessValidator


@attr.s(frozen=True, slots=True)
class InitierPropositionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    type_admission = attr.ib(type=str)
    type_financement = attr.ib(type=str)
    justification = attr.ib(type=Optional[str], default='')
    type_contrat_travail = attr.ib(type=Optional[str], default='')
    doctorat_deja_realise = attr.ib(type=str, default=ChoixDoctoratDejaRealise.NO.name)
    institution = attr.ib(type=Optional[str], default='')

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldJustificationDonneeSiPreadmission(self.type_admission, self.justification),
            ShouldTypeContratTravailDependreTypeFinancement(self.type_financement, self.type_contrat_travail),
            ShouldInstitutionDependreDoctoratRealise(self.doctorat_deja_realise, self.institution),
        ]


@attr.s(frozen=True, slots=True)
class CompletionPropositionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    type_admission = attr.ib(type=str)
    type_financement = attr.ib(type=str)
    justification = attr.ib(type=Optional[str], default='')
    type_contrat_travail = attr.ib(type=Optional[str], default='')
    doctorat_deja_realise = attr.ib(type=str, default=ChoixDoctoratDejaRealise.NO.name)
    institution = attr.ib(type=Optional[str], default='')

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldJustificationDonneeSiPreadmission(self.type_admission, self.justification),
            ShouldTypeContratTravailDependreTypeFinancement(self.type_financement, self.type_contrat_travail),
            ShouldInstitutionDependreDoctoratRealise(self.doctorat_deja_realise, self.institution),
        ]


@attr.s(frozen=True, slots=True)
class SoumettrePropositionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    proposition = attr.ib(type='Proposition')  # type: Proposition

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return []


@attr.s(frozen=True, slots=True)
class IdentifierPromoteurValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision = attr.ib(type='GroupeDeSupervision')  # type: GroupeDeSupervision
    promoteur_id = attr.ib(type='PromoteurIdentity')  # type: PromoteurIdentity

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        membre_CA_id = MembreCAIdentity(matricule=self.promoteur_id.matricule)
        return [
            ShouldPromoteurPasDejaPresentDansGroupeDeSupervision(self.groupe_de_supervision, self.promoteur_id),
            ShouldMembreCAPasDejaPresentDansGroupeDeSupervision(self.groupe_de_supervision, membre_CA_id),
        ]


@attr.s(frozen=True, slots=True)
class IdentifierMembreCAValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision = attr.ib(type='GroupeDeSupervision')  # type: GroupeDeSupervision
    membre_CA_id = attr.ib(type='MembreCAIdentity')  # type: MembreCAIdentity

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        promoteur_id = PromoteurIdentity(matricule=self.membre_CA_id.matricule)
        return [
            ShouldMembreCAPasDejaPresentDansGroupeDeSupervision(self.groupe_de_supervision, self.membre_CA_id),
            ShouldPromoteurPasDejaPresentDansGroupeDeSupervision(self.groupe_de_supervision, promoteur_id),
        ]


@attr.s(frozen=True, slots=True)
class SupprimerPromoteurValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision = attr.ib(type='GroupeDeSupervision')  # type: GroupeDeSupervision
    promoteur_id = attr.ib(type='PromoteurIdentity')  # type: PromoteurIdentity

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPromoteurEtreDansGroupeDeSupervision(self.groupe_de_supervision, self.promoteur_id),
        ]


@attr.s(frozen=True, slots=True)
class SupprimerMembreCAValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision = attr.ib(type='GroupeDeSupervision')  # type: GroupeDeSupervision
    membre_CA_id = attr.ib(type='MembreCAIdentity')  # type: MembreCAIdentity

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldMembreCAEtreDansGroupeDeSupervision(self.groupe_de_supervision, self.membre_CA_id),
        ]


@attr.s(frozen=True, slots=True)
class InviterASignerValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision = attr.ib(type='GroupeDeSupervision')  # type: GroupeDeSupervision
    signataire_id = attr.ib(type=Union['PromoteurIdentity', 'MembreCAIdentity'])

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSignataireEtreDansGroupeDeSupervision(self.groupe_de_supervision, self.signataire_id),
            ShouldSignatairePasDejaInvite(self.groupe_de_supervision, self.signataire_id),
        ]


@attr.s(frozen=True, slots=True)
class ApprouverValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision = attr.ib(type='GroupeDeSupervision')  # type: GroupeDeSupervision
    signataire_id = attr.ib(type=Union['PromoteurIdentity', 'MembreCAIdentity'])

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSignataireEtreDansGroupeDeSupervision(self.groupe_de_supervision, self.signataire_id),
            ShouldSignataireEtreInvite(self.groupe_de_supervision, self.signataire_id),
        ]


@attr.s(frozen=True, slots=True)
class DetailsProjetValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    type_admission = attr.ib(type='ChoixTypeAdmission')  # type: ChoixTypeAdmission
    projet = attr.ib(type='DetailProjet')  # type: DetailProjet

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldDetailProjetEtreComplete(self.type_admission, self.projet),
        ]


@attr.s(frozen=True, slots=True)
class CotutelleValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    cotutelle = attr.ib(type='Cotutelle')  # type: Cotutelle

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldCotutelleEtreComplete(self.cotutelle),
        ]


@attr.s(frozen=True, slots=True)
class SignatairesValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision = attr.ib(type='GroupeDeSupervision')  # type: GroupeDeSupervision

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldGroupeDeSupervisionAvoirAuMoinsUnPromoteur(self.groupe_de_supervision.signatures_promoteurs),
            ShouldGroupeDeSupervisionAvoirAuMoinsUnMembreCA(self.groupe_de_supervision.signatures_membres_CA),
        ]
