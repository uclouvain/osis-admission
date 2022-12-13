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
from typing import List, Optional, Dict

import attr

from admission.ddd.admission.formation_generale.domain.model._comptabilite import Comptabilite
from admission.ddd.admission.enums import (
    ChoixAffiliationSport,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    LienParente,
    TypeSituationAssimilation,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AffiliationsNonCompleteesException,
    AssimilationNonCompleteeException,
    ReductionDesDroitsInscriptionNonCompleteeException,
)
from base.ddd.utils.business_validator import BusinessValidator
from base.models.utils.utils import ChoiceEnum


@attr.dataclass(frozen=True, slots=True)
class ShouldReductionDesDroitsInscriptionEtreCompletee(BusinessValidator):
    demande_allocation_d_etudes_communaute_francaise_belgique: Optional[bool]
    enfant_personnel: Optional[bool]
    attestation_enfant_personnel: List[str]

    def validate(self, *args, **kwargs):
        if (
            self.demande_allocation_d_etudes_communaute_francaise_belgique is None
            or self.enfant_personnel is None
            or (self.enfant_personnel and not self.attestation_enfant_personnel)
        ):
            raise ReductionDesDroitsInscriptionNonCompleteeException


@attr.dataclass(frozen=True, slots=True)
class ShouldAssimilationEtreCompletee(BusinessValidator):
    pays_nationalite_ue: Optional[bool]
    comptabilite: Comptabilite

    DEPENDANCES_CHAMPS_ASSIMILATION: Dict[str, Dict[ChoiceEnum, List[str]]] = {
        'type_situation_assimilation': {
            TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE: [
                'sous_type_situation_assimilation_1',
            ],
            TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE: [
                'sous_type_situation_assimilation_2',
            ],
            TypeSituationAssimilation.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT: [
                'sous_type_situation_assimilation_3',
            ],
            TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS: [
                'attestation_cpas',
            ],
            TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4: [
                'relation_parente',
                'sous_type_situation_assimilation_5',
            ],
            TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2: [
                'sous_type_situation_assimilation_6',
            ],
            TypeSituationAssimilation.RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE: [
                'titre_identite_sejour_longue_duree_ue',
                'titre_sejour_belgique',
            ],
        },
        'sous_type_situation_assimilation_1': {
            ChoixAssimilation1.TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE: [
                'carte_resident_longue_duree',
            ],
            ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER: [
                'carte_cire_sejour_illimite_etranger',
            ],
            ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_MEMBRE_UE: [
                'carte_sejour_membre_ue',
            ],
            ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_PERMANENT_MEMBRE_UE: [
                'carte_sejour_permanent_membre_ue',
            ],
        },
        'sous_type_situation_assimilation_2': {
            ChoixAssimilation2.REFUGIE: [
                'carte_a_b_refugie',
            ],
            ChoixAssimilation2.DEMANDEUR_ASILE: [
                'annexe_25_26_refugies_apatrides',
                'attestation_immatriculation',
            ],
            ChoixAssimilation2.PROTECTION_SUBSIDIAIRE: [
                'carte_a_b',
                'decision_protection_subsidiaire',
            ],
            ChoixAssimilation2.PROTECTION_TEMPORAIRE: [
                'decision_protection_temporaire',
            ],
        },
        'sous_type_situation_assimilation_3': {
            ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS: [
                'titre_sejour_3_mois_professionel',
                'fiches_remuneration',
            ],
            ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT: [
                'titre_sejour_3_mois_remplacement',
                'preuve_allocations_chomage_pension_indemnite',
            ],
        },
        'relation_parente': {
            LienParente.PERE: [
                'composition_menage_acte_naissance',
            ],
            LienParente.MERE: [
                'composition_menage_acte_naissance',
            ],
            LienParente.TUTEUR_LEGAL: [
                'acte_tutelle',
            ],
            LienParente.CONJOINT: [
                'composition_menage_acte_mariage',
            ],
            LienParente.COHABITANT_LEGAL: [
                'attestation_cohabitation_legale',
            ],
        },
        'sous_type_situation_assimilation_5': {
            ChoixAssimilation5.A_NATIONALITE_UE: ['carte_identite_parent'],
            ChoixAssimilation5.TITULAIRE_TITRE_SEJOUR_LONGUE_DUREE: ['titre_sejour_longue_duree_parent'],
            ChoixAssimilation5.CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE: [
                'annexe_25_26_refugies_apatrides_decision_protection_parent'
            ],
            ChoixAssimilation5.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT: [
                'titre_sejour_3_mois_parent',
                'fiches_remuneration_parent',
            ],
            ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS: [
                'attestation_cpas_parent',
            ],
        },
        'sous_type_situation_assimilation_6': {
            ChoixAssimilation6.A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE: [
                'decision_bourse_cfwb',
            ],
            ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT: [
                'attestation_boursier',
            ],
        },
    }

    def recuperer_champs_requis(self, nom_champ) -> List[str]:
        champs_requis = self.DEPENDANCES_CHAMPS_ASSIMILATION.get(nom_champ, {}).get(
            getattr(self.comptabilite, nom_champ),
            [],
        )
        nouveaux_champs_requis = []
        for champ in champs_requis:
            if champ in self.DEPENDANCES_CHAMPS_ASSIMILATION:
                nouveaux_champs_requis += self.recuperer_champs_requis(champ)
        return champs_requis + nouveaux_champs_requis

    def validate(self, *args, **kwargs):
        if self.pays_nationalite_ue is False:

            if not self.comptabilite.type_situation_assimilation:
                raise AssimilationNonCompleteeException

            champs_requis = self.recuperer_champs_requis('type_situation_assimilation')

            if any(not getattr(self.comptabilite, champ) for champ in champs_requis):
                raise AssimilationNonCompleteeException


@attr.dataclass(frozen=True, slots=True)
class ShouldAffiliationsEtreCompletees(BusinessValidator):
    affiliation_sport: Optional[ChoixAffiliationSport]
    etudiant_solidaire: Optional[bool]

    def validate(self, *args, **kwargs):
        if not self.affiliation_sport or self.etudiant_solidaire is None:
            raise AffiliationsNonCompleteesException
