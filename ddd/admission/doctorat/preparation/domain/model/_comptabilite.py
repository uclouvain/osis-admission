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
from admission.ddd.admission.doctorat.preparation.domain.model.enums.comptabilite import (
    ChoixAffiliationSport,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    ChoixTypeCompteBancaire,
    LienParente,
    TypeSituationAssimilation,
)

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class Comptabilite(interface.ValueObject):
    # Absence de dettes
    attestation_absence_dette_etablissement: List[str] = attr.Factory(list)

    # Réduction des droits d'inscription
    demande_allocation_d_etudes_communaute_francaise_belgique: Optional[bool] = None
    enfant_personnel: Optional[bool] = None
    attestation_enfant_personnel: List[str] = attr.Factory(list)

    # Assimilation
    type_situation_assimilation: Optional[TypeSituationAssimilation] = None

    # Assimilation 1
    sous_type_situation_assimilation_1: Optional[ChoixAssimilation1] = None
    carte_resident_longue_duree: List[str] = attr.Factory(list)
    carte_cire_sejour_illimite_etranger: List[str] = attr.Factory(list)
    carte_sejour_membre_ue: List[str] = attr.Factory(list)
    carte_sejour_permanent_membre_ue: List[str] = attr.Factory(list)

    # Assimilation 2
    sous_type_situation_assimilation_2: Optional[ChoixAssimilation2] = None
    carte_a_b_refugie: List[str] = attr.Factory(list)
    annexe_25_26_refugies_apatrides: List[str] = attr.Factory(list)
    attestation_immatriculation: List[str] = attr.Factory(list)
    carte_a_b: List[str] = attr.Factory(list)
    decision_protection_subsidiaire: List[str] = attr.Factory(list)
    decision_protection_temporaire: List[str] = attr.Factory(list)

    # Assimilation 3
    sous_type_situation_assimilation_3: Optional[ChoixAssimilation3] = None
    titre_sejour_3_mois_professionel: List[str] = attr.Factory(list)
    fiches_remuneration: List[str] = attr.Factory(list)
    titre_sejour_3_mois_remplacement: List[str] = attr.Factory(list)
    preuve_allocations_chomage_pension_indemnite: List[str] = attr.Factory(list)

    # Assimilation 4
    attestation_cpas: List[str] = attr.Factory(list)

    # Assimilation 5
    relation_parente: Optional[LienParente] = None
    sous_type_situation_assimilation_5: Optional[ChoixAssimilation5] = None
    composition_menage_acte_naissance: List[str] = attr.Factory(list)
    acte_tutelle: List[str] = attr.Factory(list)
    composition_menage_acte_mariage: List[str] = attr.Factory(list)
    attestation_cohabitation_legale: List[str] = attr.Factory(list)
    carte_identite_parent: List[str] = attr.Factory(list)
    titre_sejour_longue_duree_parent: List[str] = attr.Factory(list)
    annexe_25_26_refugies_apatrides_decision_protection_parent: List[str] = attr.Factory(list)
    titre_sejour_3_mois_parent: List[str] = attr.Factory(list)
    fiches_remuneration_parent: List[str] = attr.Factory(list)
    attestation_cpas_parent: List[str] = attr.Factory(list)

    # Assimilation 6
    sous_type_situation_assimilation_6: Optional[ChoixAssimilation6] = None
    decision_bourse_cfwb: List[str] = attr.Factory(list)
    attestation_boursier: List[str] = attr.Factory(list)

    # Assimilation 7
    titre_identite_sejour_longue_duree_ue: List[str] = attr.Factory(list)
    titre_sejour_belgique: List[str] = attr.Factory(list)

    # Affiliations
    affiliation_sport: Optional[ChoixAffiliationSport] = None
    etudiant_solidaire: Optional[bool] = None

    # Compte bancaire
    type_numero_compte: Optional[ChoixTypeCompteBancaire] = None
    numero_compte_iban: Optional[str] = ''
    numero_compte_autre_format: Optional[str] = ''
    code_bic_swift_banque: Optional[str] = ''
    prenom_titulaire_compte: Optional[str] = ''
    nom_titulaire_compte: Optional[str] = ''


comptabilite_non_remplie = Comptabilite()
