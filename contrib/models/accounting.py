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
    )

    # Absence of debt
    institute_absence_debts_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Certificate stating no debts to the institution'),
    )

    # Reduced tuition fee
    french_community_study_allowance_application = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('Application for a study allowance from the French Community of Belgium'),
    )
    is_staff_child = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('Child of a member of the staff of the UCLouvain or the Martin V entity'),
    )
    staff_child_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Certificate for children of staff'),
    )

    # Assimilation
    assimilation_situation = models.CharField(
        blank=True,
        choices=TypeSituationAssimilation.choices(),
        default='',
        max_length=100,
        verbose_name=_('Belgian student status'),
    )
    assimilation_1_situation_type = models.CharField(
        blank=True,
        choices=ChoixAssimilation1.choices(),
        default='',
        max_length=64,
        verbose_name=_('Assimilation 1 situation types'),
    )
    long_term_resident_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Long-term resident card'),
    )
    cire_unlimited_stay_foreigner_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('CIRE, unlimited stay or foreigner`s card'),
    )
    ue_family_member_residence_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Residence card of a family member of a European Union citizen'),
    )
    ue_family_member_permanent_residence_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Permanent residence card of a family member of a European Union citizen'),
    )
    assimilation_2_situation_type = models.CharField(
        blank=True,
        choices=ChoixAssimilation2.choices(),
        default='',
        max_length=64,
        verbose_name=_('Assimilation 2 situation types'),
    )
    stateless_person_proof = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_(
            'Copy of official document from the local authority or Foreign Nationals Office proving stateless status',
        ),
    )
    refugee_a_b_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('A or B card with refugee mention'),
    )
    refugees_stateless_annex_25_26 = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Annex 25 or 26 for refugees and stateless persons'),
    )
    registration_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Registration certificate'),
    )
    a_b_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('A or B card'),
    )
    subsidiary_protection_decision = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Decision confirming the granting of subsidiary protection'),
    )
    a_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('A card'),
    )
    temporary_protection_decision = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Decision confirming the granting of temporary protection'),
    )
    assimilation_3_situation_type = models.CharField(
        blank=True,
        choices=ChoixAssimilation3.choices(),
        default='',
        max_length=64,
        verbose_name=_('Assimilation 3 situation types'),
    )
    professional_3_month_residence_permit = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Residence permit valid for more than 3 months with professional income'),
    )
    salary_slips = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Salary slips'),
    )
    replacement_3_month_residence_permit = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Residence permit valid for more than 3 months with replacement income'),
    )
    unemployment_benefit_pension_compensation_proof = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Proof of receipt of unemployment benefit, pension or compensation'),
    )
    cpas_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Certificate of support from the CPAS'),
    )
    relationship = models.CharField(
        blank=True,
        choices=LienParente.choices(),
        default='',
        max_length=32,
        verbose_name=_('Relationship'),
    )
    assimilation_5_situation_type = models.CharField(
        blank=True,
        choices=ChoixAssimilation5.choices(),
        default='',
        max_length=100,
        verbose_name=_('Assimilation 5 situation types'),
    )
    household_composition_or_birth_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Household composition or the birth certificate'),
    )
    tutorship_act = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Tutorship act'),
    )
    household_composition_or_marriage_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Household composition or the marriage certificate'),
    )
    legal_cohabitation_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Legal cohabitation certificate'),
    )
    parent_identity_card = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Parent identity card'),
    )
    parent_long_term_residence_permit = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Parent long-term residence permit'),
    )
    parent_refugees_stateless_annex_25_26_or_protection_decision = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_(
            'Annex 25 or 26 or the A/B card mentioning the refugee status or '
            'the decision confirming the protection of the parent'
        ),
    )
    parent_3_month_residence_permit = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Parent residence permit valid for more than 3 months'),
    )
    parent_salary_slips = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Parent salary slips'),
    )
    parent_cpas_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Parent certificate of support from the CPAS'),
    )
    assimilation_6_situation_type = models.CharField(
        blank=True,
        choices=ChoixAssimilation6.choices(),
        default='',
        max_length=64,
        verbose_name=_('Assimilation 6 situation types'),
    )
    cfwb_scholarship_decision = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('CFWB scholarship decision'),
    )
    scholarship_certificate = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Scholarship certificate'),
    )
    ue_long_term_stay_identity_document = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Identity document proving the long-term stay in a member state of the European Union'),
    )
    belgium_residence_permit = FileField(
        upload_to=admission_accounting_directory_path,
        verbose_name=_('Residence permit in Belgium'),
    )

    # Affiliation
    sport_affiliation = models.CharField(
        blank=True,
        choices=ChoixAffiliationSport.choices(),
        default='',
        max_length=32,
        verbose_name=_('Sport affiliation'),
    )
    solidarity_student = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('Solidarity student'),
    )

    # Bank account
    account_number_type = models.CharField(
        blank=True,
        choices=ChoixTypeCompteBancaire.choices(),
        default='',
        max_length=32,
        verbose_name=_('Account number type'),
    )
    iban_account_number = models.CharField(
        blank=True,
        default='',
        max_length=34,
        verbose_name=_('IBAN account number'),
    )
    valid_iban = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('The IBAN account number is valid'),
    )
    other_format_account_number = models.CharField(
        blank=True,
        default='',
        max_length=255,
        verbose_name=_('Account number'),
    )
    bic_swift_code = models.CharField(
        blank=True,
        default='',
        max_length=32,
        verbose_name=_('BIC/SWIFT code identifying the bank from which the account originates'),
    )
    account_holder_first_name = models.CharField(
        blank=True,
        default='',
        max_length=128,
        verbose_name=_('Account holder first name'),
    )
    account_holder_last_name = models.CharField(
        blank=True,
        default='',
        max_length=128,
        verbose_name=_('Account holder surname'),
    )
