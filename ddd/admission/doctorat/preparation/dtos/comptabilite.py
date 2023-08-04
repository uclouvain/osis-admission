##############################################################################
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
##############################################################################
from typing import List, Optional

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class ComptabiliteDTO(interface.DTO):
    # Absence de dettes
    attestation_absence_dette_etablissement: List[str]

    # Assimilation
    type_situation_assimilation: str

    # Assimilation 1
    sous_type_situation_assimilation_1: str
    carte_resident_longue_duree: List[str]
    carte_cire_sejour_illimite_etranger: List[str]
    carte_sejour_membre_ue: List[str]
    carte_sejour_permanent_membre_ue: List[str]

    # Assimilation 2
    sous_type_situation_assimilation_2: str
    carte_a_b_refugie: List[str]
    annexe_25_26_refugies_apatrides: List[str]
    attestation_immatriculation: List[str]
    preuve_statut_apatride: List[str]
    carte_a_b: List[str]
    decision_protection_subsidiaire: List[str]
    decision_protection_temporaire: List[str]
    carte_a: List[str]

    # Assimilation 3
    sous_type_situation_assimilation_3: str
    titre_sejour_3_mois_professionel: List[str]
    fiches_remuneration: List[str]
    titre_sejour_3_mois_remplacement: List[str]
    preuve_allocations_chomage_pension_indemnite: List[str]

    # Assimilation 4
    attestation_cpas: List[str]

    # Assimilation 5
    relation_parente: str
    sous_type_situation_assimilation_5: str
    composition_menage_acte_naissance: List[str]
    acte_tutelle: List[str]
    composition_menage_acte_mariage: List[str]
    attestation_cohabitation_legale: List[str]
    carte_identite_parent: List[str]
    titre_sejour_longue_duree_parent: List[str]
    annexe_25_26_refugies_apatrides_decision_protection_parent: List[str]
    titre_sejour_3_mois_parent: List[str]
    fiches_remuneration_parent: List[str]
    attestation_cpas_parent: List[str]

    # Assimilation 6
    sous_type_situation_assimilation_6: str
    decision_bourse_cfwb: List[str]
    attestation_boursier: List[str]

    # Assimilation 7
    titre_identite_sejour_longue_duree_ue: List[str]
    titre_sejour_belgique: List[str]

    # Affiliations
    etudiant_solidaire: Optional[bool]

    # Compte bancaire
    type_numero_compte: str
    numero_compte_iban: str
    iban_valide: Optional[bool]
    numero_compte_autre_format: str
    code_bic_swift_banque: str
    prenom_titulaire_compte: str
    nom_titulaire_compte: str


@attr.dataclass(frozen=True, slots=True)
class ConditionsComptabiliteDTO(interface.DTO):
    pays_nationalite_ue: Optional[bool]
    a_frequente_recemment_etablissement_communaute_fr: Optional[bool]


@attr.dataclass(frozen=True, slots=True)
class DerniersEtablissementsSuperieursCommunauteFrancaiseFrequentesDTO(interface.DTO):
    annee: int
    noms: List[str]
