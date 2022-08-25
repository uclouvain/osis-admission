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
import datetime
from typing import List, Optional, Union, Tuple

import attr

from admission.ddd.projet_doctoral.preparation.business_types import *
from admission.ddd.projet_doctoral.preparation.domain.model._candidat_adresse import CandidatAdresse
from admission.ddd.projet_doctoral.preparation.domain.model._candidat_signaletique import CandidatSignaletique
from admission.ddd.projet_doctoral.preparation.domain.model._cotutelle import Cotutelle
from admission.ddd.projet_doctoral.preparation.domain.model._detail_projet import DetailProjet
from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixTypeAdmission
from admission.ddd.projet_doctoral.preparation.domain.model._experience_precedente_recherche import (
    ChoixDoctoratDejaRealise,
)
from admission.ddd.projet_doctoral.preparation.domain.model._financement import Financement
from admission.ddd.projet_doctoral.preparation.domain.model._institut import InstitutIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._signature_promoteur import SignaturePromoteur
from admission.ddd.projet_doctoral.preparation.domain.validator import *
from base.ddd.utils.business_validator import BusinessValidator, TwoStepsMultipleBusinessExceptionListValidator


@attr.dataclass(frozen=True, slots=True)
class InitierPropositionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    type_admission: str
    type_financement: Optional[str] = ''
    justification: Optional[str] = ''
    type_contrat_travail: Optional[str] = ''
    doctorat_deja_realise: str = ChoixDoctoratDejaRealise.NO.name
    institution: Optional[str] = ''
    domaine_these: Optional[str] = ''

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldJustificationDonneeSiPreadmission(self.type_admission, self.justification),
            ShouldTypeContratTravailDependreTypeFinancement(self.type_financement, self.type_contrat_travail),
            ShouldInstitutionDependreDoctoratRealise(self.doctorat_deja_realise, self.institution),
            ShouldDomaineDependreDoctoratRealise(self.doctorat_deja_realise, self.domaine_these),
        ]


@attr.dataclass(frozen=True, slots=True)
class CompletionPropositionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    type_admission: str
    type_financement: Optional[str] = ''
    justification: Optional[str] = ''
    type_contrat_travail: Optional[str] = ''
    doctorat_deja_realise: str = ChoixDoctoratDejaRealise.NO.name
    institution: Optional[str] = ''
    domaine_these: Optional[str] = ''

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldJustificationDonneeSiPreadmission(self.type_admission, self.justification),
            ShouldTypeContratTravailDependreTypeFinancement(self.type_financement, self.type_contrat_travail),
            ShouldInstitutionDependreDoctoratRealise(self.doctorat_deja_realise, self.institution),
            ShouldDomaineDependreDoctoratRealise(self.doctorat_deja_realise, self.domaine_these),
        ]


@attr.dataclass(frozen=True, slots=True)
class IdentifierPromoteurValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    promoteur_id: 'PromoteurIdentity'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        membre_CA_id = MembreCAIdentity(matricule=self.promoteur_id.matricule)
        return [
            ShouldGroupeDeSupervisionNonCompletPourPromoteurs(self.groupe_de_supervision),
            ShouldPromoteurPasDejaPresentDansGroupeDeSupervision(self.groupe_de_supervision, self.promoteur_id),
            ShouldMembreCAPasDejaPresentDansGroupeDeSupervision(self.groupe_de_supervision, membre_CA_id),
        ]


@attr.dataclass(frozen=True, slots=True)
class IdentifierMembreCAValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    membre_CA_id: 'MembreCAIdentity'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        promoteur_id = PromoteurIdentity(matricule=self.membre_CA_id.matricule)
        return [
            ShouldGroupeDeSupervisionNonCompletPourMembresCA(self.groupe_de_supervision),
            ShouldMembreCAPasDejaPresentDansGroupeDeSupervision(self.groupe_de_supervision, self.membre_CA_id),
            ShouldPromoteurPasDejaPresentDansGroupeDeSupervision(self.groupe_de_supervision, promoteur_id),
        ]


@attr.dataclass(frozen=True, slots=True)
class DesignerPromoteurReferenceValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    promoteur_id: 'PromoteurIdentity'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPromoteurEtreDansGroupeDeSupervision(self.groupe_de_supervision, self.promoteur_id),
        ]


@attr.dataclass(frozen=True, slots=True)
class SupprimerPromoteurValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    promoteur_id: 'PromoteurIdentity'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPromoteurEtreDansGroupeDeSupervision(self.groupe_de_supervision, self.promoteur_id),
        ]


@attr.dataclass(frozen=True, slots=True)
class SupprimerMembreCAValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    membre_CA_id: 'MembreCAIdentity'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldMembreCAEtreDansGroupeDeSupervision(self.groupe_de_supervision, self.membre_CA_id),
        ]


@attr.dataclass(frozen=True, slots=True)
class InviterASignerValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    signataire_id: Union['PromoteurIdentity', 'MembreCAIdentity']

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSignataireEtreDansGroupeDeSupervision(self.groupe_de_supervision, self.signataire_id),
            ShouldSignatairePasDejaInvite(self.groupe_de_supervision, self.signataire_id),
        ]


@attr.dataclass(frozen=True, slots=True)
class ApprouverValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    signataire_id: Union['PromoteurIdentity', 'MembreCAIdentity']

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSignataireEtreDansGroupeDeSupervision(self.groupe_de_supervision, self.signataire_id),
            ShouldSignataireEtreInvite(self.groupe_de_supervision, self.signataire_id),
        ]


@attr.dataclass(frozen=True, slots=True)
class ProjetDoctoralValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    type_admission: 'ChoixTypeAdmission'
    projet: 'DetailProjet'
    financement: 'Financement'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldProjetEtreComplet(self.type_admission, self.projet, self.financement),
        ]


@attr.dataclass(frozen=True, slots=True)
class IdentificationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    identite_signaletique: 'CandidatSignaletique'

    date_naissance: Optional[datetime.date]
    annee_naissance: Optional[int]

    numero_registre_national_belge: Optional[str]
    numero_carte_identite: Optional[str]
    carte_identite: List[str]
    numero_passeport: Optional[str]
    passeport: List[str]
    date_expiration_passeport: Optional[datetime.date]

    noma_derniere_inscription_ucl: Optional[str]
    annee_derniere_inscription_ucl: Optional[int]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSignaletiqueCandidatEtreCompletee(
                signaletique=self.identite_signaletique,
            ),
            ShouldCandidatSpecifierNomOuPrenom(
                nom=self.identite_signaletique.nom,
                prenom=self.identite_signaletique.prenom,
            ),
            ShouldCandidatSpecifierNumeroIdentite(
                numero_registre_national_belge=self.numero_registre_national_belge,
                numero_carte_identite=self.numero_carte_identite,
                numero_passeport=self.numero_passeport,
            ),
            ShouldCandidatBelgeSpecifierNumeroRegistreNationalBelge(
                numero_registre_national_belge=self.numero_registre_national_belge,
                pays_nationalite=self.identite_signaletique.pays_nationalite,
            ),
            ShouldCandidatSpecifierDateOuAnneeNaissance(
                date_naissance=self.date_naissance,
                annee_naissance=self.annee_naissance,
            ),
            ShouldCandidatAuthentiquerPasseport(
                numero_passeport=self.numero_passeport,
                date_expiration_passeport=self.date_expiration_passeport,
                passeport=self.passeport,
            ),
            ShouldCandidatAuthentiquerIdentite(
                numero_registre_national_belge=self.numero_registre_national_belge,
                numero_carte_identite=self.numero_carte_identite,
                carte_identite=self.carte_identite,
            ),
            ShouldCandidatSpecifierNOMASiDejaInscrit(
                noma_derniere_inscription_ucl=self.noma_derniere_inscription_ucl,
                annee_derniere_inscription_ucl=self.annee_derniere_inscription_ucl,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class CoordonneesValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    domicile_legal: Optional['CandidatAdresse']
    adresse_correspondance: Optional['CandidatAdresse']

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldAdresseDomicileLegalCandidatEtreCompletee(
                adresse=self.domicile_legal,
            ),
            ShouldAdresseCorrespondanceEtreCompleteeSiSpecifiee(adresse=self.adresse_correspondance),
        ]


@attr.dataclass(frozen=True, slots=True)
class LanguesConnuesValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    codes_langues_connues: List[str]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldLanguesConnuesRequisesEtreSpecifiees(
                codes_langues_connues=self.codes_langues_connues,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class CurriculumValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    fichier_pdf: List[str]
    annee_courante: int
    annee_derniere_inscription_ucl: Optional[int]
    annee_diplome_etudes_secondaires_belges: Optional[int]
    annee_diplome_etudes_secondaires_etrangeres: Optional[int]
    dates_experiences_non_academiques: List[Tuple[datetime.date, datetime.date]]
    annees_experiences_academiques: List[int]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldCurriculumFichierEtreSpecifie(
                fichier_pdf=self.fichier_pdf,
            ),
            ShouldAnneesCVRequisesCompletees(
                annee_courante=self.annee_courante,
                annees_experiences_academiques=self.annees_experiences_academiques,
                annee_derniere_inscription_ucl=self.annee_derniere_inscription_ucl,
                annee_diplome_etudes_secondaires_belges=self.annee_diplome_etudes_secondaires_belges,
                annee_diplome_etudes_secondaires_etrangeres=self.annee_diplome_etudes_secondaires_etrangeres,
                dates_experiences_non_academiques=self.dates_experiences_non_academiques,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class CotutelleValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    cotutelle: Optional['Cotutelle']

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldCotutelleEtreComplete(self.cotutelle),
        ]


@attr.dataclass(frozen=True, slots=True)
class SignatairesValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldGroupeDeSupervisionAvoirAuMoinsUnMembreCA(self.groupe_de_supervision.signatures_membres_CA),
            ShouldGroupeDeSupervisionAvoirUnPromoteurDeReference(self.groupe_de_supervision),
        ]


@attr.dataclass(frozen=True, slots=True)
class ApprobationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldDemandeSignatureLancee(self.groupe_de_supervision.statut_signature),
            ShouldPromoteursOntApprouve(self.groupe_de_supervision.signatures_promoteurs),
            ShouldMembresCAOntApprouve(self.groupe_de_supervision.signatures_membres_CA),
        ]


@attr.dataclass(frozen=True, slots=True)
class ApprobationPromoteurValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    signatures_promoteurs: List['SignaturePromoteur']
    signataire: Union['PromoteurIdentity', 'MembreCAIdentity']
    proposition_institut_these: Optional[InstitutIdentity]
    institut_these: Optional[str]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPremierPromoteurRenseignerInstitutThese(
                self.signatures_promoteurs,
                self.signataire,
                self.proposition_institut_these,
                self.institut_these,
            ),
        ]
