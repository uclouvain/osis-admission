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
from typing import List, Optional, Union, Dict

import attr

from admission.ddd.admission.doctorat.preparation.business_types import *
from admission.ddd.admission.doctorat.preparation.domain.model._comptabilite import Comptabilite
from admission.ddd.admission.doctorat.preparation.domain.model._cotutelle import Cotutelle
from admission.ddd.admission.doctorat.preparation.domain.model._detail_projet import DetailProjet
from admission.ddd.admission.doctorat.preparation.domain.model._financement import Financement
from admission.ddd.admission.doctorat.preparation.domain.model._institut import InstitutIdentity
from admission.ddd.admission.doctorat.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.admission.doctorat.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.admission.doctorat.preparation.domain.model._signature_promoteur import SignaturePromoteur
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixDoctoratDejaRealise, ChoixTypeAdmission
from admission.ddd.admission.doctorat.preparation.domain.validator import *
from admission.ddd.admission.domain.validator import (
    ShouldAnneesCVRequisesCompletees,
    ShouldAbsenceDeDetteEtreCompletee,
    ShouldIBANCarteBancaireRemboursementEtreCompletee,
    ShouldAutreFormatCarteBancaireRemboursementEtreCompletee,
    ShouldExperiencesAcademiquesEtreCompletees,
    ShouldTypeCompteBancaireRemboursementEtreComplete,
    ShouldAssimilationEtreCompletee,
)
from base.ddd.utils.business_validator import BusinessValidator, TwoStepsMultipleBusinessExceptionListValidator
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceAcademiqueDTO, ExperienceNonAcademiqueDTO


@attr.dataclass(frozen=True, slots=True)
class InitierPropositionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    type_admission: str
    justification: Optional[str] = ''

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldJustificationDonneeSiPreadmission(self.type_admission, self.justification),
        ]


@attr.dataclass(frozen=True, slots=True)
class ModifierTypeAdmissionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    type_admission: str
    justification: Optional[str] = ''

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldJustificationDonneeSiPreadmission(self.type_admission, self.justification),
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
    matricule: Optional[str]
    prenom: Optional[str]
    nom: Optional[str]
    email: Optional[str]
    institution: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    langue: Optional[str]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldGroupeDeSupervisionNonCompletPourPromoteurs(self.groupe_de_supervision),
            ShouldMembreEtreInterneOuExterne(
                self.matricule,
                self.prenom,
                self.nom,
                self.email,
                self.institution,
                self.ville,
                self.pays,
                self.langue,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class IdentifierMembreCAValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    matricule: Optional[str]
    prenom: Optional[str]
    nom: Optional[str]
    email: Optional[str]
    institution: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    langue: Optional[str]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldGroupeDeSupervisionNonCompletPourMembresCA(self.groupe_de_supervision),
            ShouldMembreEtreInterneOuExterne(
                self.matricule,
                self.prenom,
                self.nom,
                self.email,
                self.institution,
                self.ville,
                self.pays,
                self.langue,
            ),
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
    annee_diplome_etudes_secondaires: Optional[int]
    experiences_non_academiques: List[ExperienceNonAcademiqueDTO]
    experiences_academiques: List[ExperienceAcademiqueDTO]
    experiences_academiques_incompletes: Dict[str, str]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldCurriculumFichierEtreSpecifie(
                fichier_pdf=self.fichier_pdf,
            ),
            ShouldExperiencesAcademiquesEtreCompletees(
                experiences_academiques_incompletes=self.experiences_academiques_incompletes,
            ),
            ShouldAnneesCVRequisesCompletees(
                annee_courante=self.annee_courante,
                experiences_academiques=self.experiences_academiques,
                experiences_academiques_incompletes=self.experiences_academiques_incompletes,
                annee_derniere_inscription_ucl=self.annee_derniere_inscription_ucl,
                annee_diplome_etudes_secondaires=self.annee_diplome_etudes_secondaires,
                experiences_non_academiques=self.experiences_non_academiques,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class ComptabiliteValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    pays_nationalite_ue: Optional[bool]
    a_frequente_recemment_etablissement_communaute_fr: Optional[bool]
    comptabilite: Comptabilite

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldAbsenceDeDetteEtreCompletee(
                attestation_absence_dette_etablissement=self.comptabilite.attestation_absence_dette_etablissement,
                a_frequente_recemment_etablissement_communaute_fr=(
                    self.a_frequente_recemment_etablissement_communaute_fr
                ),
            ),
            ShouldAssimilationEtreCompletee(
                pays_nationalite_ue=self.pays_nationalite_ue,
                comptabilite=self.comptabilite,
            ),
            ShouldAffiliationsEtreCompletees(
                etudiant_solidaire=self.comptabilite.etudiant_solidaire,
            ),
            ShouldTypeCompteBancaireRemboursementEtreComplete(
                type_numero_compte=self.comptabilite.type_numero_compte,
            ),
            ShouldIBANCarteBancaireRemboursementEtreCompletee(
                type_numero_compte=self.comptabilite.type_numero_compte,
                numero_compte_iban=self.comptabilite.numero_compte_iban,
                prenom_titulaire_compte=self.comptabilite.prenom_titulaire_compte,
                nom_titulaire_compte=self.comptabilite.nom_titulaire_compte,
            ),
            ShouldAutreFormatCarteBancaireRemboursementEtreCompletee(
                type_numero_compte=self.comptabilite.type_numero_compte,
                numero_compte_autre_format=self.comptabilite.numero_compte_autre_format,
                code_bic_swift_banque=self.comptabilite.code_bic_swift_banque,
                prenom_titulaire_compte=self.comptabilite.prenom_titulaire_compte,
                nom_titulaire_compte=self.comptabilite.nom_titulaire_compte,
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
    promoteur_reference: Optional[PromoteurIdentity]
    proposition_institut_these: Optional[InstitutIdentity]
    institut_these: Optional[str]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPromoteurReferenceRenseignerInstitutThese(
                self.signatures_promoteurs,
                self.signataire,
                self.promoteur_reference,
                self.proposition_institut_these,
                self.institut_these,
            ),
        ]
