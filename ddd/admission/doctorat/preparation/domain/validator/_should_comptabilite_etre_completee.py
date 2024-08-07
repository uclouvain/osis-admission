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

from typing import List, Optional, Union, Dict

import attr

from admission.ddd.admission.doctorat.preparation.domain.model._comptabilite import Comptabilite as ComptabiliteDoctorat
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AbsenceDeDetteNonCompleteeDoctoratException,
    CarteBancaireRemboursementAutreFormatNonCompleteDoctoratException,
    CarteBancaireRemboursementIbanNonCompleteDoctoratException,
    TypeCompteBancaireRemboursementNonCompleteDoctoratException,
    AssimilationNonCompleteeDoctoratException,
    AffiliationsNonCompleteesDoctoratException,
)
from admission.ddd.admission.dtos.resume import AdmissionComptabiliteDTO
from admission.ddd.admission.enums import (
    ChoixTypeCompteBancaire,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    LienParente,
    TypeSituationAssimilation,
)
from admission.ddd.admission.formation_generale.domain.model._comptabilite import Comptabilite as ComptabiliteGenerale
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldAffiliationsEtreCompletees(BusinessValidator):
    etudiant_solidaire: Optional[bool]

    def validate(self, *args, **kwargs):
        if self.etudiant_solidaire is None:
            raise AffiliationsNonCompleteesDoctoratException


@attr.dataclass(frozen=True, slots=True)
class ShouldAbsenceDeDetteEtreCompletee(BusinessValidator):
    attestation_absence_dette_etablissement: List[str]
    a_frequente_recemment_etablissement_communaute_fr: Optional[bool]

    def validate(self, *args, **kwargs):
        if self.a_frequente_recemment_etablissement_communaute_fr and not self.attestation_absence_dette_etablissement:
            raise AbsenceDeDetteNonCompleteeDoctoratException


@attr.dataclass(frozen=True, slots=True)
class ShouldTypeCompteBancaireRemboursementEtreComplete(BusinessValidator):
    type_numero_compte: Optional[ChoixTypeCompteBancaire]

    def validate(self, *args, **kwargs):
        if not self.type_numero_compte:
            raise TypeCompteBancaireRemboursementNonCompleteDoctoratException


@attr.dataclass(frozen=True, slots=True)
class ShouldIBANCarteBancaireRemboursementEtreCompletee(BusinessValidator):
    type_numero_compte: Optional[ChoixTypeCompteBancaire]
    numero_compte_iban: Optional[str]
    prenom_titulaire_compte: Optional[str]
    nom_titulaire_compte: Optional[str]

    def validate(self, *args, **kwargs):
        if self.type_numero_compte == ChoixTypeCompteBancaire.IBAN and any(
            not champ
            for champ in [
                self.numero_compte_iban,
                self.prenom_titulaire_compte,
                self.nom_titulaire_compte,
            ]
        ):
            raise CarteBancaireRemboursementIbanNonCompleteDoctoratException


@attr.dataclass(frozen=True, slots=True)
class ShouldAutreFormatCarteBancaireRemboursementEtreCompletee(BusinessValidator):
    type_numero_compte: Optional[ChoixTypeCompteBancaire]
    numero_compte_autre_format: Optional[str]
    code_bic_swift_banque: Optional[str]
    prenom_titulaire_compte: Optional[str]
    nom_titulaire_compte: Optional[str]

    def validate(self, *args, **kwargs):
        if self.type_numero_compte == ChoixTypeCompteBancaire.AUTRE_FORMAT and any(
            not champ
            for champ in [
                self.numero_compte_autre_format,
                self.code_bic_swift_banque,
                self.prenom_titulaire_compte,
                self.nom_titulaire_compte,
            ]
        ):
            raise CarteBancaireRemboursementAutreFormatNonCompleteDoctoratException


DEPENDANCES_CHAMPS_ASSIMILATION: Dict[str, Dict[str, List[str]]] = {
    'type_situation_assimilation': {
        TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE.name: [
            'sous_type_situation_assimilation_1',
        ],
        TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name: [
            'sous_type_situation_assimilation_2',
        ],
        TypeSituationAssimilation.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT.name: [
            'sous_type_situation_assimilation_3',
        ],
        TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name: [
            'attestation_cpas',
        ],
        TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4.name: [
            'relation_parente',
            'sous_type_situation_assimilation_5',
        ],
        TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2.name: [
            'sous_type_situation_assimilation_6',
        ],
        TypeSituationAssimilation.RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE.name: [
            'titre_identite_sejour_longue_duree_ue',
            'titre_sejour_belgique',
        ],
    },
    'sous_type_situation_assimilation_1': {
        ChoixAssimilation1.TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE.name: [
            'carte_resident_longue_duree',
        ],
        ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name: [
            'carte_cire_sejour_illimite_etranger',
        ],
        ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_MEMBRE_UE.name: [
            'carte_sejour_membre_ue',
        ],
        ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_PERMANENT_MEMBRE_UE.name: [
            'carte_sejour_permanent_membre_ue',
        ],
    },
    'sous_type_situation_assimilation_2': {
        ChoixAssimilation2.REFUGIE.name: [
            'carte_a_b_refugie',
        ],
        ChoixAssimilation2.DEMANDEUR_ASILE.name: [
            'annexe_25_26_refugies_apatrides',
            'attestation_immatriculation',
        ],
        ChoixAssimilation2.APATRIDE.name: [
            'preuve_statut_apatride',
        ],
        ChoixAssimilation2.PROTECTION_SUBSIDIAIRE.name: [
            'carte_a_b',
            'decision_protection_subsidiaire',
        ],
        ChoixAssimilation2.PROTECTION_TEMPORAIRE.name: [
            'decision_protection_temporaire',
            'carte_a',
        ],
    },
    'sous_type_situation_assimilation_3': {
        ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS.name: [
            'titre_sejour_3_mois_professionel',
            'fiches_remuneration',
        ],
        ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT.name: [
            'titre_sejour_3_mois_remplacement',
            'preuve_allocations_chomage_pension_indemnite',
        ],
    },
    'relation_parente': {
        LienParente.PERE.name: [
            'composition_menage_acte_naissance',
        ],
        LienParente.MERE.name: [
            'composition_menage_acte_naissance',
        ],
        LienParente.TUTEUR_LEGAL.name: [
            'acte_tutelle',
        ],
        LienParente.CONJOINT.name: [
            'composition_menage_acte_mariage',
        ],
        LienParente.COHABITANT_LEGAL.name: [
            'attestation_cohabitation_legale',
        ],
    },
    'sous_type_situation_assimilation_5': {
        ChoixAssimilation5.A_NATIONALITE_UE.name: ['carte_identite_parent'],
        ChoixAssimilation5.TITULAIRE_TITRE_SEJOUR_LONGUE_DUREE.name: ['titre_sejour_longue_duree_parent'],
        ChoixAssimilation5.CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name: [
            'annexe_25_26_refugies_apatrides_decision_protection_parent'
        ],
        ChoixAssimilation5.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT.name: [
            'titre_sejour_3_mois_parent',
            'fiches_remuneration_parent',
        ],
        ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name: [
            'attestation_cpas_parent',
        ],
    },
    'sous_type_situation_assimilation_6': {
        ChoixAssimilation6.A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE.name: [
            'decision_bourse_cfwb',
        ],
        ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name: [
            'attestation_boursier',
        ],
    },
}


@attr.dataclass(frozen=True, slots=True)
class ShouldAssimilationEtreCompletee(BusinessValidator):
    pays_nationalite_ue: Optional[bool]
    comptabilite: Union[ComptabiliteGenerale, ComptabiliteDoctorat]

    def recuperer_champs_requis(self, nom_champ) -> List[str]:
        """Récuperer les champs d'assimilation qui sont requis à partir du nom d'un champ et des données."""
        valeur_champ = getattr(self.comptabilite, nom_champ)
        champs_requis = DEPENDANCES_CHAMPS_ASSIMILATION.get(nom_champ, {}).get(
            valeur_champ and valeur_champ.name,
            [],
        )
        nouveaux_champs_requis = []
        for champ in champs_requis:
            if champ in DEPENDANCES_CHAMPS_ASSIMILATION:
                nouveaux_champs_requis += self.recuperer_champs_requis(champ)
        return champs_requis + nouveaux_champs_requis

    def validate(self, *args, **kwargs):
        if self.pays_nationalite_ue is False:

            if not self.comptabilite.type_situation_assimilation:
                raise AssimilationNonCompleteeDoctoratException

            champs_requis = self.recuperer_champs_requis('type_situation_assimilation')

            if any(not getattr(self.comptabilite, champ) for champ in champs_requis):
                raise AssimilationNonCompleteeDoctoratException
