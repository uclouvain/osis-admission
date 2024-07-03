# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db import models
from django.utils.translation import gettext_lazy as _
from osis_document.contrib import FileField

from admission.contrib.models.base import BaseAdmission
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


def admission_accounting_directory_path(accounting, filename: str):
    """Return the file upload directory path."""
    return 'admission/{}/{}/accounting/{}'.format(
        accounting.admission.candidate.uuid,
        accounting.admission.uuid,
        filename,
    )


class Accounting(models.Model):
    admission = models.OneToOneField(
        BaseAdmission,
        on_delete=models.CASCADE,
        related_name='accounting',
        unique=True,
        #db_comment='Lien dans le contexte de formation generale et dans doctorat'
    )

    # Absence of debt
    institute_absence_debts_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Certificate stating no debts to the institution'),
        # db_comment='Proposition.comptabilite.attestation_absence_dette_etablissement'
    )

    # Reduced tuition fee
    french_community_study_allowance_application = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('Application for a study allowance from the French Community of Belgium'),
        # db_comment='Proposition.comptabilite.demande_allocation_d_etudes_communaute_francaise_belgique'
    )
    is_staff_child = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('Child of a member of the staff of the UCLouvain or the Martin V entity'),
        # db_comment='Proposition.comptabilite.enfant_personnel'
    )
    staff_child_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Certificate for children of staff'),
        # db_comment='Proposition.comptabilite.attestation_enfant_personnel'
    )

    # Assimilation
    assimilation_situation = models.CharField(
        blank=True,
        choices=TypeSituationAssimilation.choices(),
        default='',
        max_length=100,
        verbose_name=_('Belgian student status'),
        # db_comment='Proposition.comptabilite.type_situation_assimilation'
    )
    assimilation_1_situation_type = models.CharField(
        blank=True,
        choices=ChoixAssimilation1.choices(),
        default='',
        max_length=64,
        verbose_name=_('Assimilation 1 situation types'),
        # db_comment='Proposition.comptabilite.sous_type_situation_assimilation_1'
    )
    long_term_resident_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Long-term resident card'),
        # db_comment='Proposition.comptabilite.carte_resident_longue_duree'
    )
    cire_unlimited_stay_foreigner_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('CIRE, unlimited stay or foreigner`s card'),
        # db_comment='Proposition.comptabilite.carte_cire_sejour_illimite_etranger'
    )
    ue_family_member_residence_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Residence card of a family member of a European Union citizen'),
        # db_comment='Proposition.comptabilite.carte_sejour_membre_ue'
    )
    ue_family_member_permanent_residence_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Permanent residence card of a family member of a European Union citizen'),
        # db_comment='Proposition.comptabilite.carte_sejour_permanent_membre_ue'
    )
    assimilation_2_situation_type = models.CharField(
        blank=True,
        choices=ChoixAssimilation2.choices(),
        default='',
        max_length=64,
        verbose_name=_('Assimilation 2 situation types'),
        # db_comment='Proposition.comptabilite.sous_type_situation_assimilation_2'
    )
    stateless_person_proof = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_(
            'Copy of official document from the local authority or Foreign Nationals Office proving stateless status',
        ),
        # db_comment='Proposition.comptabilite.preuve_statut_apatride'
    )
    refugee_a_b_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('A or B card with refugee mention'),
        # db_comment='Proposition.comptabilite.carte_a_b_refugie'
    )
    refugees_stateless_annex_25_26 = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Annex 25 or 26 for refugees and stateless persons'),
        # db_comment='Proposition.comptabilite.annexe_25_26_refugies_apatrides'
    )
    registration_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Registration certificate'),
        # db_comment='Proposition.comptabilite.attestation_immatriculation'
    )
    a_b_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('A or B card'),
        # db_comment='Proposition.comptabilite.carte_a_b'
    )
    subsidiary_protection_decision = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Decision confirming the granting of subsidiary protection'),
        # db_comment='Proposition.comptabilite.decision_protection_subsidiaire'
    )
    a_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('A card'),
        # db_comment='Proposition.comptabilite.carte_a'
    )
    temporary_protection_decision = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Decision confirming the granting of temporary protection'),
        # db_comment='Proposition.comptabilite.decision_protection_temporaire'
    )
    assimilation_3_situation_type = models.CharField(
        blank=True,
        choices=ChoixAssimilation3.choices(),
        default='',
        max_length=64,
        verbose_name=_('Assimilation 3 situation types'),
        # db_comment='Proposition.comptabilite.sous_type_situation_assimilation_3'
    )
    professional_3_month_residence_permit = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Residence permit valid for more than 3 months with professional income'),
        # db_comment='Proposition.comptabilite.sous_type_situation_assimilation_3'
    )
    salary_slips = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Salary slips'),
        # db_comment='Proposition.comptabilite.fiches_remuneration'
    )
    replacement_3_month_residence_permit = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Residence permit valid for more than 3 months with replacement income'),
        # db_comment='Proposition.comptabilite.titre_sejour_3_mois_remplacement'
    )
    unemployment_benefit_pension_compensation_proof = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Proof of receipt of unemployment benefit, pension or compensation'),
        # db_comment='Proposition.comptabilite.unemployment_benefit_pension_proof'
    )
    cpas_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Certificate of support from the CPAS'),
        # db_comment='Proposition.comptabilite.attestation_cpas'
    )
    relationship = models.CharField(
        blank=True,
        choices=LienParente.choices(),
        default='',
        max_length=32,
        verbose_name=_('Relationship'),
        # db_comment='Proposition.comptabilite.relation_parente'
    )
    assimilation_5_situation_type = models.CharField(
        blank=True,
        choices=ChoixAssimilation5.choices(),
        default='',
        max_length=100,
        verbose_name=_('Assimilation 5 situation types'),
        # db_comment='Proposition.comptabilite.sous_type_situation_assimilation_5'
    )
    household_composition_or_birth_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Household composition or the birth certificate'),
        # db_comment='Proposition.comptabilite.composition_menage_acte_naissance'
    )
    tutorship_act = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Tutorship act'),
        # db_comment='Proposition.comptabilite.acte_tutelle'
    )
    household_composition_or_marriage_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Household composition or the marriage certificate'),
        # db_comment='Proposition.comptabilite.composition_menage_acte_mariage'
    )
    legal_cohabitation_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Legal cohabitation certificate'),
        # db_comment='Proposition.comptabilite.attestation_cohabitation_legale'
    )
    parent_identity_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Parent identity card'),
        # db_comment='Proposition.comptabilite.carte_identite_parent'
    )
    parent_long_term_residence_permit = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Parent long-term residence permit'),
        # db_comment='Proposition.comptabilite.parent_long_term_residence_permit'
    )
    parent_refugees_stateless_annex_25_26_or_protection_decision = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_(
            'Annex 25 or 26 or the A/B card mentioning the refugee status or '
            'the decision confirming the protection of the parent'
        ),
         # db_comment='Proposition.comptabilite.parent_annex_25_26'
    )
    parent_3_month_residence_permit = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Parent residence permit valid for more than 3 months'),
         # db_comment='Proposition.comptabilite.titre_sejour_3_mois_parent'
    )
    parent_salary_slips = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Parent salary slips'),
         # db_comment='Proposition.comptabilite.fiches_remuneration_parent'
    )
    parent_cpas_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Parent certificate of support from the CPAS'),
         # db_comment='Proposition.comptabilite.attestation_cpas_parent'
    )
    assimilation_6_situation_type = models.CharField(
        blank=True,
        choices=ChoixAssimilation6.choices(),
        default='',
        max_length=64,
        verbose_name=_('Assimilation 6 situation types'),
         # db_comment='Proposition.comptabilite.sous_type_situation_assimilation_6'
    )
    cfwb_scholarship_decision = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('CFWB scholarship decision'),
         # db_comment='Proposition.comptabilite.decision_bourse_cfwb'
    )
    scholarship_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Scholarship certificate'),
         # db_comment='Proposition.comptabilite.attestation_boursier'
    )
    ue_long_term_stay_identity_document = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Identity document proving the long-term stay in a member state of the European Union'),
        # db_comment='Proposition.comptabilite.titre_identite_sejour_longue_duree_ue'
    )
    belgium_residence_permit = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Residence permit in Belgium'),
         # db_comment='Proposition.comptabilite.titre_sejour_belgique'
    )

    # Affiliation
    sport_affiliation = models.CharField(
        blank=True,
        choices=ChoixAffiliationSport.choices(),
        default='',
        max_length=32,
        verbose_name=_('Sport affiliation'),
        # db_comment='Proposition.comptabilite.affiliation_sport'
    )
    solidarity_student = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('Solidarity student'),
        # db_comment='Proposition.comptabilite.etudiant_solidaire'
    )

    # Bank account
    account_number_type = models.CharField(
        blank=True,
        choices=ChoixTypeCompteBancaire.choices(),
        default='',
        max_length=32,
        verbose_name=_('Account number type'),
        # db_comment='Proposition.comptabilite.type_numero_compte'
    )
    iban_account_number = models.CharField(
        blank=True,
        default='',
        max_length=34,
        verbose_name=_('IBAN account number'),
        # db_comment='Proposition.comptabilite.numero_compte_iban'
    )
    valid_iban = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('The IBAN account number is valid'),
        # db_comment='Proposition.comptabilite.iban_valide'
    )
    other_format_account_number = models.CharField(
        blank=True,
        default='',
        max_length=255,
        verbose_name=_('Account number'),
        # db_comment='Proposition.comptabilite.numero_compte_autre_format'
    )
    bic_swift_code = models.CharField(
        blank=True,
        default='',
        max_length=32,
        verbose_name=_('BIC/SWIFT code identifying the bank from which the account originates'),
        # db_comment='Proposition.comptabilite.code_bic_swift_banque'
    )
    account_holder_first_name = models.CharField(
        blank=True,
        default='',
        max_length=128,
        verbose_name=_('Account holder first name'),
        # db_comment='Proposition.comptabilite.prenom_titulaire_compte'
    )
    account_holder_last_name = models.CharField(
        blank=True,
        default='',
        max_length=128,
        verbose_name=_('Account holder surname'),
        # db_comment='Proposition.comptabilite.nom_titulaire_compte'
    )
