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
from admission.contrib.models import GeneralEducationAdmission
from admission.ddd.admission.formation_generale.domain.model._comptabilite import (
    Comptabilite,
    comptabilite_non_remplie,
)
from admission.ddd.admission.enums import (
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


def get_accounting_from_admission(admission: GeneralEducationAdmission) -> Comptabilite:
    accounting = getattr(admission, 'accounting', None)

    if not accounting:
        return comptabilite_non_remplie

    fr_be_study_allowance_application = accounting.french_community_study_allowance_application
    parent_refugees_stateless_annex_25_26 = accounting.parent_refugees_stateless_annex_25_26_or_protection_decision

    return Comptabilite(
        attestation_absence_dette_etablissement=accounting.institute_absence_debts_certificate,
        demande_allocation_d_etudes_communaute_francaise_belgique=fr_be_study_allowance_application,
        enfant_personnel=accounting.is_staff_child,
        attestation_enfant_personnel=accounting.staff_child_certificate,
        type_situation_assimilation=getattr(TypeSituationAssimilation, accounting.assimilation_situation, None),
        sous_type_situation_assimilation_1=getattr(
            ChoixAssimilation1,
            accounting.assimilation_1_situation_type,
            None,
        ),
        carte_resident_longue_duree=accounting.long_term_resident_card,
        carte_cire_sejour_illimite_etranger=accounting.cire_unlimited_stay_foreigner_card,
        carte_sejour_membre_ue=accounting.ue_family_member_residence_card,
        carte_sejour_permanent_membre_ue=accounting.ue_family_member_permanent_residence_card,
        sous_type_situation_assimilation_2=getattr(
            ChoixAssimilation2,
            accounting.assimilation_2_situation_type,
            None,
        ),
        carte_a_b_refugie=accounting.refugee_a_b_card,
        annexe_25_26_refugies_apatrides=accounting.refugees_stateless_annex_25_26,
        attestation_immatriculation=accounting.registration_certificate,
        carte_a_b=accounting.a_b_card,
        decision_protection_subsidiaire=accounting.subsidiary_protection_decision,
        decision_protection_temporaire=accounting.temporary_protection_decision,
        sous_type_situation_assimilation_3=getattr(
            ChoixAssimilation3,
            accounting.assimilation_3_situation_type,
            None,
        ),
        titre_sejour_3_mois_professionel=accounting.professional_3_month_residence_permit,
        fiches_remuneration=accounting.salary_slips,
        titre_sejour_3_mois_remplacement=accounting.replacement_3_month_residence_permit,
        preuve_allocations_chomage_pension_indemnite=accounting.unemployment_benefit_pension_compensation_proof,
        attestation_cpas=accounting.cpas_certificate,
        relation_parente=getattr(
            LienParente,
            accounting.relationship,
            None,
        ),
        sous_type_situation_assimilation_5=getattr(
            ChoixAssimilation5,
            accounting.assimilation_5_situation_type,
            None,
        ),
        composition_menage_acte_naissance=accounting.household_composition_or_birth_certificate,
        acte_tutelle=accounting.tutorship_act,
        composition_menage_acte_mariage=accounting.household_composition_or_marriage_certificate,
        attestation_cohabitation_legale=accounting.legal_cohabitation_certificate,
        carte_identite_parent=accounting.parent_identity_card,
        titre_sejour_longue_duree_parent=accounting.parent_long_term_residence_permit,
        annexe_25_26_refugies_apatrides_decision_protection_parent=parent_refugees_stateless_annex_25_26,
        titre_sejour_3_mois_parent=accounting.parent_3_month_residence_permit,
        fiches_remuneration_parent=accounting.parent_salary_slips,
        attestation_cpas_parent=accounting.parent_cpas_certificate,
        sous_type_situation_assimilation_6=getattr(
            ChoixAssimilation6,
            accounting.assimilation_6_situation_type,
            None,
        ),
        decision_bourse_cfwb=accounting.cfwb_scholarship_decision,
        attestation_boursier=accounting.scholarship_certificate,
        titre_identite_sejour_longue_duree_ue=accounting.ue_long_term_stay_identity_document,
        titre_sejour_belgique=accounting.belgium_residence_permit,
        affiliation_sport=getattr(ChoixAffiliationSport, accounting.sport_affiliation, None),
        etudiant_solidaire=accounting.solidarity_student,
        type_numero_compte=getattr(ChoixTypeCompteBancaire, accounting.account_number_type, None),
        numero_compte_iban=accounting.iban_account_number,
        iban_valide=accounting.valid_iban,
        numero_compte_autre_format=accounting.other_format_account_number,
        code_bic_swift_banque=accounting.bic_swift_code,
        prenom_titulaire_compte=accounting.account_holder_first_name,
        nom_titulaire_compte=accounting.account_holder_last_name,
    )
