# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Optional, Dict

import attr

from admission.ddd.admission.domain.model.complement_formation import ComplementFormationIdentity
from admission.ddd.admission.domain.model.condition_complementaire_approbation import (
    ConditionComplementaireApprobationIdentity,
    ConditionComplementaireLibreApprobation,
)
from admission.ddd.admission.domain.model.formation import Formation
from admission.ddd.admission.domain.model.motif_refus import MotifRefusIdentity
from admission.ddd.admission.domain.model.poste_diplomatique import PosteDiplomatiqueIdentity
from admission.ddd.admission.domain.model.titre_acces_selectionnable import TitreAccesSelectionnable
from admission.ddd.admission.domain.validator import (
    ShouldAnneesCVRequisesCompletees,
    ShouldAbsenceDeDetteEtreCompletee,
    ShouldIBANCarteBancaireRemboursementEtreCompletee,
    ShouldAutreFormatCarteBancaireRemboursementEtreCompletee,
    ShouldExperiencesAcademiquesEtreCompletees,
    ShouldTypeCompteBancaireRemboursementEtreComplete,
    ShouldAssimilationEtreCompletee,
)
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model._comptabilite import Comptabilite
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
    BesoinDeDerogation,
)
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    StatutsChecklistGenerale,
    StatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.validator import (
    ShouldCurriculumFichierEtreSpecifie,
    ShouldEquivalenceEtreSpecifiee,
    ShouldReductionDesDroitsInscriptionEtreCompletee,
    ShouldAffiliationsEtreCompletees,
    ShouldSpecifieSiDiplomeEtudesSecondaires,
    ShouldSpecifieSiDiplomeEtudesSecondairesPourBachelier,
    ShouldDiplomeBelgesEtudesSecondairesEtreComplete,
    ShouldDiplomeEtrangerEtudesSecondairesEtreComplete,
    ShouldAlternativeSecondairesEtreCompletee,
    ShouldSICPeutSoumettreAFacLorsDeLaDecisionFacultaire,
    ShouldSpecifierMotifRefusFacultaire,
    ShouldFacPeutDonnerDecision,
    ShouldSpecifierInformationsAcceptationFacultaire,
    ShouldPeutSpecifierInformationsDecisionFacultaire,
    ShouldFacPeutSoumettreAuSicLorsDeLaDecisionFacultaire,
    ShouldVisaEtreComplete,
    ShouldTitreAccesEtreSelectionne,
    ShouldConditionAccesEtreSelectionne,
    ShouldSicPeutSoumettreAuSicLorsDeLaDecisionFacultaire,
    ShouldSelectionnerTitreAccesPourEnvoyerASIC,
    ShouldPropositionEtreInscriptionTardiveAvecConditionAcces,
    ShouldComplementsFormationEtreVidesSiPasDeComplementsFormation,
    ShouldDemandeEtreTypeAdmission,
    ShouldSpecifierInformationsAcceptationFacultaireInscription,
)
from admission.ddd.admission.formation_generale.domain.validator._should_informations_checklist_etre_completees import (
    ShouldSicPeutDonnerDecision,
    ShouldParcoursAnterieurEtreSuffisant,
    ShouldNePasAvoirDeDocumentReclameImmediat,
    ShouldChecklistEtreDansEtatCorrectPourApprouverInscription,
    ShouldFinancabiliteEtreDansEtatCorrectPourApprouverDemande,
)
from base.ddd.utils.business_validator import BusinessValidator, TwoStepsMultipleBusinessExceptionListValidator
from base.models.enums.education_group_types import TrainingType
from ddd.logic.shared_kernel.profil.dtos.etudes_secondaires import (
    DiplomeBelgeEtudesSecondairesDTO,
    DiplomeEtrangerEtudesSecondairesDTO,
    AlternativeSecondairesDTO,
)
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceAcademiqueDTO, ExperienceNonAcademiqueDTO
from ddd.logic.shared_kernel.profil.dtos.parcours_interne import ExperienceParcoursInterneDTO
from epc.models.enums.condition_acces import ConditionAcces


@attr.dataclass(frozen=True, slots=True)
class FormationGeneraleCurriculumValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    fichier_pdf: List[str]
    annee_courante: int
    annee_derniere_inscription_ucl: Optional[int]
    annee_diplome_etudes_secondaires: Optional[int]
    experiences_non_academiques: List[ExperienceNonAcademiqueDTO]
    experiences_academiques: List[ExperienceAcademiqueDTO]
    experiences_academiques_incompletes: Dict[str, str]
    type_formation: TrainingType
    equivalence_diplome: List[str]
    sigle_formation: str

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldCurriculumFichierEtreSpecifie(
                fichier_pdf=self.fichier_pdf,
                type_formation=self.type_formation,
            ),
            ShouldAnneesCVRequisesCompletees(
                annee_courante=self.annee_courante,
                experiences_academiques=self.experiences_academiques,
                experiences_academiques_incompletes=self.experiences_academiques_incompletes,
                annee_derniere_inscription_ucl=self.annee_derniere_inscription_ucl,
                annee_diplome_etudes_secondaires=self.annee_diplome_etudes_secondaires,
                experiences_non_academiques=self.experiences_non_academiques,
            ),
            ShouldExperiencesAcademiquesEtreCompletees(
                experiences_academiques_incompletes=self.experiences_academiques_incompletes,
            ),
            ShouldEquivalenceEtreSpecifiee(
                equivalence=self.equivalence_diplome,
                type_formation=self.type_formation,
                experiences_academiques=self.experiences_academiques,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class FormationGeneraleCurriculumPostSoumissionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    annee_soumission: int
    date_soumission: datetime.date
    annee_diplome_etudes_secondaires: Optional[int]
    experiences_non_academiques: List[ExperienceNonAcademiqueDTO]
    experiences_academiques: List[ExperienceAcademiqueDTO]
    experiences_parcours_interne: List[ExperienceParcoursInterneDTO]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldAnneesCVRequisesCompletees(
                annee_courante=self.annee_soumission,
                experiences_academiques=self.experiences_academiques,
                experiences_academiques_incompletes={},
                annee_derniere_inscription_ucl=None,
                annee_diplome_etudes_secondaires=self.annee_diplome_etudes_secondaires,
                experiences_non_academiques=self.experiences_non_academiques,
                date_reference=self.date_soumission,
                experiences_parcours_interne=self.experiences_parcours_interne,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class FormationGeneraleComptabiliteValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    pays_nationalite_ue: Optional[bool]
    a_frequente_recemment_etablissement_communaute_fr: Optional[bool]
    comptabilite: Comptabilite
    formation: Formation

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        demande_allocation_etudes_fr_be = self.comptabilite.demande_allocation_d_etudes_communaute_francaise_belgique
        return [
            ShouldAbsenceDeDetteEtreCompletee(
                attestation_absence_dette_etablissement=self.comptabilite.attestation_absence_dette_etablissement,
                a_frequente_recemment_etablissement_communaute_fr=(
                    self.a_frequente_recemment_etablissement_communaute_fr
                ),
            ),
            ShouldReductionDesDroitsInscriptionEtreCompletee(
                demande_allocation_d_etudes_communaute_francaise_belgique=demande_allocation_etudes_fr_be,
                enfant_personnel=self.comptabilite.enfant_personnel,
            ),
            ShouldAssimilationEtreCompletee(
                pays_nationalite_ue=self.pays_nationalite_ue,
                comptabilite=self.comptabilite,
            ),
            ShouldAffiliationsEtreCompletees(
                affiliation_sport=self.comptabilite.affiliation_sport,
                etudiant_solidaire=self.comptabilite.etudiant_solidaire,
                formation=self.formation,
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
class EtudesSecondairesValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    diplome_etudes_secondaires: str
    annee_diplome_etudes_secondaires: Optional[int]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSpecifieSiDiplomeEtudesSecondaires(
                diplome_etudes_secondaires=self.diplome_etudes_secondaires,
                annee_diplome_etudes_secondaires=self.annee_diplome_etudes_secondaires,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class BachelierEtudesSecondairesValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    diplome_belge: Optional[DiplomeBelgeEtudesSecondairesDTO]
    diplome_etranger: Optional[DiplomeEtrangerEtudesSecondairesDTO]
    alternative_secondaires: Optional[AlternativeSecondairesDTO]
    diplome_etudes_secondaires: str
    annee_diplome_etudes_secondaires: Optional[int]
    est_potentiel_vae: bool
    formation: Formation

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSpecifieSiDiplomeEtudesSecondairesPourBachelier(
                diplome_etudes_secondaires=self.diplome_etudes_secondaires,
                annee_diplome_etudes_secondaires=self.annee_diplome_etudes_secondaires,
                diplome_belge=self.diplome_belge,
                diplome_etranger=self.diplome_etranger,
                alternative_secondaires=self.alternative_secondaires,
                est_potentiel_vae=self.est_potentiel_vae,
            ),
            ShouldDiplomeBelgesEtudesSecondairesEtreComplete(
                diplome_etudes_secondaires=self.diplome_etudes_secondaires,
                diplome_belge=self.diplome_belge,
            ),
            ShouldDiplomeEtrangerEtudesSecondairesEtreComplete(
                diplome_etudes_secondaires=self.diplome_etudes_secondaires,
                diplome_etranger=self.diplome_etranger,
                formation=self.formation,
            ),
            ShouldAlternativeSecondairesEtreCompletee(
                diplome_etudes_secondaires=self.diplome_etudes_secondaires,
                alternative_secondaires=self.alternative_secondaires,
                est_potentiel_vae=self.est_potentiel_vae,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class SICPeutSoumettreAFacLorsDeLaDecisionFacultaireValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutPropositionGenerale

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSICPeutSoumettreAFacLorsDeLaDecisionFacultaire(
                statut=self.statut,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class FacPeutSoumettreAuSicLorsDeLaDecisionFacultaireValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutPropositionGenerale
    checklist_actuelle: StatutsChecklistGenerale

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldFacPeutSoumettreAuSicLorsDeLaDecisionFacultaire(
                statut=self.statut,
                checklist_actuelle=self.checklist_actuelle,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class SicPeutSoumettreAuSicLorsDeLaDecisionFacultaireValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutPropositionGenerale

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [ShouldSicPeutSoumettreAuSicLorsDeLaDecisionFacultaire(statut=self.statut)]


@attr.dataclass(frozen=True, slots=True)
class RefuserParFacValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutPropositionGenerale
    motifs_refus: List[MotifRefusIdentity]
    autres_motifs_refus: List[str]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldFacPeutDonnerDecision(
                statut=self.statut,
            ),
            ShouldSpecifierMotifRefusFacultaire(
                motifs_refus=self.motifs_refus,
                autres_motifs_refus=self.autres_motifs_refus,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class RefuserParSicValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutPropositionGenerale
    motifs_refus: List[MotifRefusIdentity]
    autres_motifs_refus: List[str]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSicPeutDonnerDecision(
                statut=self.statut,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class ApprouverParFacValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutPropositionGenerale

    avec_conditions_complementaires: Optional[bool]
    conditions_complementaires_existantes: List[ConditionComplementaireApprobationIdentity]
    conditions_complementaires_libres: List[ConditionComplementaireLibreApprobation]

    avec_complements_formation: Optional[bool]
    complements_formation: Optional[List[ComplementFormationIdentity]]

    nombre_annees_prevoir_programme: Optional[int]

    titres_selectionnes: List[TitreAccesSelectionnable]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldFacPeutDonnerDecision(
                statut=self.statut,
            ),
            ShouldSpecifierInformationsAcceptationFacultaire(
                avec_conditions_complementaires=self.avec_conditions_complementaires,
                conditions_complementaires_existantes=self.conditions_complementaires_existantes,
                conditions_complementaires_libres=self.conditions_complementaires_libres,
                avec_complements_formation=self.avec_complements_formation,
                complements_formation=self.complements_formation,
                nombre_annees_prevoir_programme=self.nombre_annees_prevoir_programme,
            ),
            ShouldSelectionnerTitreAccesPourEnvoyerASIC(
                titres_selectionnes=self.titres_selectionnes,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class ApprouverInscriptionTardiveParFacValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutPropositionGenerale

    est_inscription_tardive: bool
    condition_acces: Optional[ConditionAcces]

    titres_selectionnes: List[TitreAccesSelectionnable]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldFacPeutDonnerDecision(
                statut=self.statut,
            ),
            ShouldPropositionEtreInscriptionTardiveAvecConditionAcces(
                est_inscription_tardive=self.est_inscription_tardive,
                condition_acces=self.condition_acces,
            ),
            ShouldSelectionnerTitreAccesPourEnvoyerASIC(
                titres_selectionnes=self.titres_selectionnes,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class ApprouverAdmissionParSicValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutPropositionGenerale

    avec_conditions_complementaires: Optional[bool]
    conditions_complementaires_existantes: List[ConditionComplementaireApprobationIdentity]
    conditions_complementaires_libres: List[ConditionComplementaireLibreApprobation]

    avec_complements_formation: Optional[bool]
    complements_formation: Optional[List[ComplementFormationIdentity]]

    nombre_annees_prevoir_programme: Optional[int]

    checklist: StatutsChecklistGenerale
    documents_dto: List[EmplacementDocumentDTO]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSicPeutDonnerDecision(
                statut=self.statut,
            ),
            ShouldFinancabiliteEtreDansEtatCorrectPourApprouverDemande(
                checklist_actuelle=self.checklist,
            ),
            ShouldSpecifierInformationsAcceptationFacultaire(
                avec_conditions_complementaires=self.avec_conditions_complementaires,
                conditions_complementaires_existantes=self.conditions_complementaires_existantes,
                conditions_complementaires_libres=self.conditions_complementaires_libres,
                avec_complements_formation=self.avec_complements_formation,
                complements_formation=self.complements_formation,
                nombre_annees_prevoir_programme=self.nombre_annees_prevoir_programme,
            ),
            ShouldParcoursAnterieurEtreSuffisant(
                statut=self.checklist.parcours_anterieur,
            ),
            ShouldNePasAvoirDeDocumentReclameImmediat(
                documents_dto=self.documents_dto,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class ApprouverInscriptionParSicValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutPropositionGenerale

    checklist: StatutsChecklistGenerale
    besoin_de_derogation: BesoinDeDerogation

    avec_conditions_complementaires: Optional[bool]
    conditions_complementaires_existantes: List[ConditionComplementaireApprobationIdentity]
    conditions_complementaires_libres: List[ConditionComplementaireLibreApprobation]

    documents_dto: List[EmplacementDocumentDTO]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSicPeutDonnerDecision(
                statut=self.statut,
            ),
            ShouldFinancabiliteEtreDansEtatCorrectPourApprouverDemande(
                checklist_actuelle=self.checklist,
            ),
            ShouldChecklistEtreDansEtatCorrectPourApprouverInscription(
                checklist_actuelle=self.checklist,
                besoin_de_derogation=self.besoin_de_derogation,
            ),
            ShouldSpecifierInformationsAcceptationFacultaireInscription(
                avec_conditions_complementaires=self.avec_conditions_complementaires,
                conditions_complementaires_existantes=self.conditions_complementaires_existantes,
                conditions_complementaires_libres=self.conditions_complementaires_libres,
            ),
            ShouldParcoursAnterieurEtreSuffisant(
                statut=self.checklist.parcours_anterieur,
            ),
            ShouldNePasAvoirDeDocumentReclameImmediat(
                documents_dto=self.documents_dto,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class ModifierStatutChecklistParcoursAnterieurValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutChecklist

    titres_acces_selectionnes: List[TitreAccesSelectionnable]

    condition_acces: Optional[ConditionAcces]
    millesime_condition_acces: Optional[int]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldTitreAccesEtreSelectionne(
                statut=self.statut,
                titres_acces_selectionnes=self.titres_acces_selectionnes,
            ),
            ShouldConditionAccesEtreSelectionne(
                statut=self.statut,
                condition_acces=self.condition_acces,
                millesime_condition_acces=self.millesime_condition_acces,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class SpecifierConditionAccesParcoursAnterieurValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    avec_complements_formation: Optional[bool]

    complements_formation: Optional[List[ComplementFormationIdentity]]
    commentaire_complements_formation: str

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldComplementsFormationEtreVidesSiPasDeComplementsFormation(
                avec_complements_formation=self.avec_complements_formation,
                complements_formation=self.complements_formation,
                commentaire_complements_formation=self.commentaire_complements_formation,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class SpecifierNouvellesInformationsDecisionFacultaireValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutPropositionGenerale

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPeutSpecifierInformationsDecisionFacultaire(
                statut=self.statut,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class FormationGeneraleInformationsComplementairesValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    pays_nationalite: str
    pays_nationalite_europeen: Optional[bool]
    pays_residence: str

    poste_diplomatique: Optional[PosteDiplomatiqueIdentity]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldVisaEtreComplete(
                pays_nationalite=self.pays_nationalite,
                pays_nationalite_europeen=self.pays_nationalite_europeen,
                pays_residence=self.pays_residence,
                poste_diplomatique=self.poste_diplomatique,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class ApprouverParSicAValiderValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutPropositionGenerale
    statut_checklist_parcours_anterieur: StatutChecklist
    documents_dto: List[EmplacementDocumentDTO]
    type_demande: TypeDemande

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSicPeutDonnerDecision(
                statut=self.statut,
            ),
            ShouldParcoursAnterieurEtreSuffisant(
                statut=self.statut_checklist_parcours_anterieur,
            ),
            ShouldNePasAvoirDeDocumentReclameImmediat(
                documents_dto=self.documents_dto,
            ),
            ShouldDemandeEtreTypeAdmission(
                type_demande=self.type_demande,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class SpecifierInformationsApprobationInscriptionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutPropositionGenerale

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSicPeutDonnerDecision(statut=self.statut),
        ]


@attr.dataclass(frozen=True, slots=True)
class RefuserParSicAValiderValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutPropositionGenerale

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSicPeutDonnerDecision(
                statut=self.statut,
            ),
        ]
