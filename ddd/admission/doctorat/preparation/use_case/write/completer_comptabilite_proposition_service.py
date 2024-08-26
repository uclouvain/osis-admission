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
from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.commands import CompleterComptabilitePropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository


def completer_comptabilite_proposition(
    cmd: 'CompleterComptabilitePropositionCommand',
    proposition_repository: 'IPropositionRepository',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_entity_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition_candidat = proposition_repository.get(entity_id=proposition_entity_id)

    # WHEN
    proposition_candidat.completer_comptabilite(
        auteur_modification=cmd.auteur_modification,
        attestation_absence_dette_etablissement=cmd.attestation_absence_dette_etablissement,
        type_situation_assimilation=cmd.type_situation_assimilation,
        sous_type_situation_assimilation_1=cmd.sous_type_situation_assimilation_1,
        carte_resident_longue_duree=cmd.carte_resident_longue_duree,
        carte_cire_sejour_illimite_etranger=cmd.carte_cire_sejour_illimite_etranger,
        carte_sejour_membre_ue=cmd.carte_sejour_membre_ue,
        carte_sejour_permanent_membre_ue=cmd.carte_sejour_permanent_membre_ue,
        sous_type_situation_assimilation_2=cmd.sous_type_situation_assimilation_2,
        carte_a_b_refugie=cmd.carte_a_b_refugie,
        annexe_25_26_refugies_apatrides=cmd.annexe_25_26_refugies_apatrides,
        attestation_immatriculation=cmd.attestation_immatriculation,
        preuve_statut_apatride=cmd.preuve_statut_apatride,
        carte_a_b=cmd.carte_a_b,
        decision_protection_subsidiaire=cmd.decision_protection_subsidiaire,
        decision_protection_temporaire=cmd.decision_protection_temporaire,
        carte_a=cmd.carte_a,
        sous_type_situation_assimilation_3=cmd.sous_type_situation_assimilation_3,
        titre_sejour_3_mois_professionel=cmd.titre_sejour_3_mois_professionel,
        fiches_remuneration=cmd.fiches_remuneration,
        titre_sejour_3_mois_remplacement=cmd.titre_sejour_3_mois_remplacement,
        preuve_allocations_chomage_pension_indemnite=cmd.preuve_allocations_chomage_pension_indemnite,
        attestation_cpas=cmd.attestation_cpas,
        relation_parente=cmd.relation_parente,
        sous_type_situation_assimilation_5=cmd.sous_type_situation_assimilation_5,
        composition_menage_acte_naissance=cmd.composition_menage_acte_naissance,
        acte_tutelle=cmd.acte_tutelle,
        composition_menage_acte_mariage=cmd.composition_menage_acte_mariage,
        attestation_cohabitation_legale=cmd.attestation_cohabitation_legale,
        carte_identite_parent=cmd.carte_identite_parent,
        titre_sejour_longue_duree_parent=cmd.titre_sejour_longue_duree_parent,
        annexe_25_26_protection_parent=cmd.annexe_25_26_refugies_apatrides_decision_protection_parent,
        titre_sejour_3_mois_parent=cmd.titre_sejour_3_mois_parent,
        fiches_remuneration_parent=cmd.fiches_remuneration_parent,
        attestation_cpas_parent=cmd.attestation_cpas_parent,
        sous_type_situation_assimilation_6=cmd.sous_type_situation_assimilation_6,
        decision_bourse_cfwb=cmd.decision_bourse_cfwb,
        attestation_boursier=cmd.attestation_boursier,
        titre_identite_sejour_longue_duree_ue=cmd.titre_identite_sejour_longue_duree_ue,
        titre_sejour_belgique=cmd.titre_sejour_belgique,
        etudiant_solidaire=cmd.etudiant_solidaire,
        type_numero_compte=cmd.type_numero_compte,
        numero_compte_iban=cmd.numero_compte_iban,
        iban_valide=cmd.iban_valide,
        numero_compte_autre_format=cmd.numero_compte_autre_format,
        code_bic_swift_banque=cmd.code_bic_swift_banque,
        prenom_titulaire_compte=cmd.prenom_titulaire_compte,
        nom_titulaire_compte=cmd.nom_titulaire_compte,
    )

    # THEN
    proposition_repository.save(proposition_candidat)

    return proposition_entity_id
