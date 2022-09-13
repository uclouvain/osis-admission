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
from admission.ddd.projet_doctoral.preparation.domain.model._comptabilite import Comptabilite
from admission.ddd.projet_doctoral.preparation.dtos import ComptabiliteDTO


def get_dto_accounting_from_domain_model(comptabilite: 'Comptabilite') -> 'ComptabiliteDTO':
    demande_allocation_fr = comptabilite.demande_allocation_d_etudes_communaute_francaise_belgique
    annexe_25_26_parent = comptabilite.annexe_25_26_refugies_apatrides_decision_protection_parent

    return ComptabiliteDTO(
        attestation_absence_dette_etablissement=comptabilite.attestation_absence_dette_etablissement,
        demande_allocation_d_etudes_communaute_francaise_belgique=demande_allocation_fr,
        enfant_personnel=comptabilite.enfant_personnel,
        attestation_enfant_personnel=comptabilite.attestation_enfant_personnel,
        type_situation_assimilation=comptabilite.type_situation_assimilation.name
        if comptabilite.type_situation_assimilation
        else '',
        sous_type_situation_assimilation_1=comptabilite.sous_type_situation_assimilation_1.name
        if comptabilite.sous_type_situation_assimilation_1
        else '',
        carte_resident_longue_duree=comptabilite.carte_resident_longue_duree,
        carte_cire_sejour_illimite_etranger=comptabilite.carte_cire_sejour_illimite_etranger,
        carte_sejour_membre_ue=comptabilite.carte_sejour_membre_ue,
        carte_sejour_permanent_membre_ue=comptabilite.carte_sejour_permanent_membre_ue,
        sous_type_situation_assimilation_2=comptabilite.sous_type_situation_assimilation_2.name
        if comptabilite.sous_type_situation_assimilation_2
        else '',
        carte_a_b_refugie=comptabilite.carte_a_b_refugie,
        annexe_25_26_refugies_apatrides=comptabilite.annexe_25_26_refugies_apatrides,
        attestation_immatriculation=comptabilite.attestation_immatriculation,
        carte_a_b=comptabilite.carte_a_b,
        decision_protection_subsidiaire=comptabilite.decision_protection_subsidiaire,
        decision_protection_temporaire=comptabilite.decision_protection_temporaire,
        sous_type_situation_assimilation_3=comptabilite.sous_type_situation_assimilation_3.name
        if comptabilite.sous_type_situation_assimilation_3
        else '',
        titre_sejour_3_mois_professionel=comptabilite.titre_sejour_3_mois_professionel,
        fiches_remuneration=comptabilite.fiches_remuneration,
        titre_sejour_3_mois_remplacement=comptabilite.titre_sejour_3_mois_remplacement,
        preuve_allocations_chomage_pension_indemnite=comptabilite.preuve_allocations_chomage_pension_indemnite,
        attestation_cpas=comptabilite.attestation_cpas,
        relation_parente=comptabilite.relation_parente.name
        if comptabilite.relation_parente
        else '',
        sous_type_situation_assimilation_5=comptabilite.sous_type_situation_assimilation_5.name
        if comptabilite.sous_type_situation_assimilation_5
        else '',
        composition_menage_acte_naissance=comptabilite.composition_menage_acte_naissance,
        acte_tutelle=comptabilite.acte_tutelle,
        composition_menage_acte_mariage=comptabilite.composition_menage_acte_mariage,
        attestation_cohabitation_legale=comptabilite.attestation_cohabitation_legale,
        carte_identite_parent=comptabilite.carte_identite_parent,
        titre_sejour_longue_duree_parent=comptabilite.titre_sejour_longue_duree_parent,
        annexe_25_26_refugies_apatrides_decision_protection_parent=annexe_25_26_parent,
        titre_sejour_3_mois_parent=comptabilite.titre_sejour_3_mois_parent,
        fiches_remuneration_parent=comptabilite.fiches_remuneration_parent,
        attestation_cpas_parent=comptabilite.attestation_cpas_parent,
        sous_type_situation_assimilation_6=comptabilite.sous_type_situation_assimilation_6.name
        if comptabilite.sous_type_situation_assimilation_6
        else '',
        decision_bourse_cfwb=comptabilite.decision_bourse_cfwb,
        attestation_boursier=comptabilite.attestation_boursier,
        titre_identite_sejour_longue_duree_ue=comptabilite.titre_identite_sejour_longue_duree_ue,
        titre_sejour_belgique=comptabilite.titre_sejour_belgique,
        affiliation_sport=comptabilite.affiliation_sport.name
        if comptabilite.affiliation_sport
        else '',
        etudiant_solidaire=comptabilite.etudiant_solidaire,
        type_numero_compte=comptabilite.type_numero_compte.name
        if comptabilite.type_numero_compte
        else '',
        numero_compte_iban=comptabilite.numero_compte_iban,
        numero_compte_autre_format=comptabilite.numero_compte_autre_format,
        code_bic_swift_banque=comptabilite.code_bic_swift_banque,
        prenom_titulaire_compte=comptabilite.prenom_titulaire_compte,
        nom_titulaire_compte=comptabilite.nom_titulaire_compte,
    )
