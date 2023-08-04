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
from admission.contrib.models import Accounting
from admission.ddd.admission.doctorat.preparation.domain.service.i_comptabilite import IComptabiliteTranslator
from admission.ddd.admission.doctorat.preparation.dtos import ComptabiliteDTO


class ComptabiliteTranslator(IComptabiliteTranslator):
    @classmethod
    def get_comptabilite_dto(cls, proposition_uuid: str) -> ComptabiliteDTO:
        accounting = Accounting.objects.get(admission__uuid=proposition_uuid)

        parent_25_26_annex = accounting.parent_refugees_stateless_annex_25_26_or_protection_decision

        return ComptabiliteDTO(
            attestation_absence_dette_etablissement=accounting.institute_absence_debts_certificate,
            type_situation_assimilation=accounting.assimilation_situation,
            sous_type_situation_assimilation_1=accounting.assimilation_1_situation_type,
            carte_resident_longue_duree=accounting.long_term_resident_card,
            carte_cire_sejour_illimite_etranger=accounting.cire_unlimited_stay_foreigner_card,
            carte_sejour_membre_ue=accounting.ue_family_member_residence_card,
            carte_sejour_permanent_membre_ue=accounting.ue_family_member_permanent_residence_card,
            sous_type_situation_assimilation_2=accounting.assimilation_2_situation_type,
            carte_a_b_refugie=accounting.refugee_a_b_card,
            annexe_25_26_refugies_apatrides=accounting.refugees_stateless_annex_25_26,
            attestation_immatriculation=accounting.registration_certificate,
            preuve_statut_apatride=accounting.stateless_person_proof,
            carte_a_b=accounting.a_b_card,
            decision_protection_subsidiaire=accounting.subsidiary_protection_decision,
            decision_protection_temporaire=accounting.temporary_protection_decision,
            carte_a=accounting.a_card,
            sous_type_situation_assimilation_3=accounting.assimilation_3_situation_type,
            titre_sejour_3_mois_professionel=accounting.professional_3_month_residence_permit,
            fiches_remuneration=accounting.salary_slips,
            titre_sejour_3_mois_remplacement=accounting.replacement_3_month_residence_permit,
            preuve_allocations_chomage_pension_indemnite=accounting.unemployment_benefit_pension_compensation_proof,
            attestation_cpas=accounting.cpas_certificate,
            relation_parente=accounting.relationship,
            sous_type_situation_assimilation_5=accounting.assimilation_5_situation_type,
            composition_menage_acte_naissance=accounting.household_composition_or_birth_certificate,
            acte_tutelle=accounting.tutorship_act,
            composition_menage_acte_mariage=accounting.household_composition_or_marriage_certificate,
            attestation_cohabitation_legale=accounting.legal_cohabitation_certificate,
            carte_identite_parent=accounting.parent_identity_card,
            titre_sejour_longue_duree_parent=accounting.parent_long_term_residence_permit,
            annexe_25_26_refugies_apatrides_decision_protection_parent=parent_25_26_annex,
            titre_sejour_3_mois_parent=accounting.parent_3_month_residence_permit,
            fiches_remuneration_parent=accounting.parent_salary_slips,
            attestation_cpas_parent=accounting.parent_cpas_certificate,
            sous_type_situation_assimilation_6=accounting.assimilation_6_situation_type,
            decision_bourse_cfwb=accounting.cfwb_scholarship_decision,
            attestation_boursier=accounting.scholarship_certificate,
            titre_identite_sejour_longue_duree_ue=accounting.ue_long_term_stay_identity_document,
            titre_sejour_belgique=accounting.belgium_residence_permit,
            etudiant_solidaire=accounting.solidarity_student,
            type_numero_compte=accounting.account_number_type,
            numero_compte_iban=accounting.iban_account_number,
            iban_valide=accounting.valid_iban,
            numero_compte_autre_format=accounting.other_format_account_number,
            code_bic_swift_banque=accounting.bic_swift_code,
            prenom_titulaire_compte=accounting.account_holder_first_name,
            nom_titulaire_compte=accounting.account_holder_last_name,
        )
