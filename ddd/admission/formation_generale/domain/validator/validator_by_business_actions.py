# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Optional, Tuple, Dict

import attr

from admission.ddd.admission.doctorat.preparation.dtos.curriculum import ExperienceAcademiqueDTO
from admission.ddd.admission.domain.validator import (
    ShouldAnneesCVRequisesCompletees,
    ShouldAbsenceDeDetteEtreCompletee,
    ShouldIBANCarteBancaireRemboursementEtreCompletee,
    ShouldAutreFormatCarteBancaireRemboursementEtreCompletee,
    ShouldExperiencesAcademiquesEtreCompletees,
    ShouldTypeCompteBancaireRemboursementEtreComplete,
    ShouldAssimilationEtreCompletee,
)
from admission.ddd.admission.formation_generale.domain.model._comptabilite import Comptabilite
from admission.ddd.admission.domain.model.formation import Formation
from admission.ddd.admission.dtos.etudes_secondaires import (
    DiplomeBelgeEtudesSecondairesDTO,
    DiplomeEtrangerEtudesSecondairesDTO,
    AlternativeSecondairesDTO,
)
from admission.ddd.admission.formation_generale.domain.validator import (
    ShouldCurriculumFichierEtreSpecifie,
    ShouldEquivalenceEtreSpecifiee,
    ShouldContinuationCycleBachelierEtreSpecifiee,
    ShouldAttestationContinuationCycleBachelierEtreSpecifiee,
    ShouldReductionDesDroitsInscriptionEtreCompletee,
    ShouldAffiliationsEtreCompletees,
    ShouldSpecifieSiDiplomeEtudesSecondaires,
    ShouldSpecifieSiDiplomeEtudesSecondairesPourBachelier,
    ShouldDiplomeBelgesEtudesSecondairesEtreComplete,
    ShouldDiplomeEtrangerEtudesSecondairesEtreComplete,
    ShouldAlternativeSecondairesEtreCompletee,
)
from base.ddd.utils.business_validator import BusinessValidator, TwoStepsMultipleBusinessExceptionListValidator
from base.models.enums.education_group_types import TrainingType


@attr.dataclass(frozen=True, slots=True)
class FormationGeneraleCurriculumValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    fichier_pdf: List[str]
    annee_courante: int
    annee_derniere_inscription_ucl: Optional[int]
    annee_diplome_etudes_secondaires: Optional[int]
    dates_experiences_non_academiques: List[Tuple[datetime.date, datetime.date]]
    experiences_academiques: List[ExperienceAcademiqueDTO]
    experiences_academiques_incompletes: Dict[str, str]
    type_formation: TrainingType
    continuation_cycle_bachelier: Optional[bool]
    attestation_continuation_cycle_bachelier: List[str]
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
                dates_experiences_non_academiques=self.dates_experiences_non_academiques,
            ),
            ShouldExperiencesAcademiquesEtreCompletees(
                experiences_academiques_incompletes=self.experiences_academiques_incompletes,
            ),
            ShouldEquivalenceEtreSpecifiee(
                equivalence=self.equivalence_diplome,
                type_formation=self.type_formation,
                experiences_academiques=self.experiences_academiques,
            ),
            ShouldContinuationCycleBachelierEtreSpecifiee(
                continuation_cycle_bachelier=self.continuation_cycle_bachelier,
                type_formation=self.type_formation,
                experiences_academiques=self.experiences_academiques,
            ),
            ShouldAttestationContinuationCycleBachelierEtreSpecifiee(
                continuation_cycle_bachelier=self.continuation_cycle_bachelier,
                attestation_continuation_cycle_bachelier=self.attestation_continuation_cycle_bachelier,
                sigle_formation=self.sigle_formation,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class FormationGeneraleComptabiliteValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    pays_nationalite_ue: Optional[bool]
    a_frequente_recemment_etablissement_communaute_fr: Optional[bool]
    comptabilite: Comptabilite

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
                attestation_enfant_personnel=self.comptabilite.attestation_enfant_personnel,
            ),
            ShouldAssimilationEtreCompletee(
                pays_nationalite_ue=self.pays_nationalite_ue,
                comptabilite=self.comptabilite,
            ),
            ShouldAffiliationsEtreCompletees(
                affiliation_sport=self.comptabilite.affiliation_sport,
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
