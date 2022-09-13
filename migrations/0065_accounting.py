# Generated by Django 3.2.12 on 2022-09-19 18:00

from django.db import migrations, models
import django.db.models.deletion
import osis_document.contrib.fields


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0064_scholarship_data_thesis_domain'),
    ]

    operations = [
        migrations.CreateModel(
            name='Accounting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('institute_absence_debts_certificate', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Certificate stating the absence of debts towards the institute')),
                ('french_community_study_allowance_application', models.BooleanField(blank=True, null=True, verbose_name='Application for a study allowance from the French Community of Belgium')),
                ('is_staff_child', models.BooleanField(blank=True, null=True, verbose_name='Child of a member of the staff of the UCLouvain or the Martin V entity')),
                ('staff_child_certificate', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Staff child certificate')),
                ('assimilation_situation', models.CharField(blank=True, choices=[('AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE', 'I have a settlement permit or I am a long-term resident in Belgium (assimilation 1)'), ('REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE', 'I am a refugee, stateless person, or have been granted a subsidiary or temporary protection (assimilation 2)'), ('AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT', 'I have a residence permit for more than 3 months, and I also have professional or replacement income (assimilation 3)'), ('PRIS_EN_CHARGE_OU_DESIGNE_CPAS', 'I am supported by the CPAS, or by a CPAS rest home or designated by the CPAS (assimilation 4)'), ('PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4', 'My father, mother, legal tutor, spouse or legal cohabitant has the nationality of a country of a Member State of the European Union, or fulfills the conditions referred to by one of the assimilations from 1 to 4 (assimilation 5)'), ('A_BOURSE_ARTICLE_105_PARAGRAPH_2', 'I benefit from a grant covered by the paragraph 2 of article 105 of the decree of 7 November 2013 (assimilation 6)'), ('RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE', 'I am a long-term resident in the European Union outside Belgium (assimilation 7)'), ('AUCUNE_ASSIMILATION', 'None of these proposals are relevant to me')], default='', max_length=100, verbose_name='Assimilation situation')),
                ('assimilation_1_situation_type', models.CharField(blank=True, choices=[('TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE', 'I have a long-term resident card'), ('TITULAIRE_CARTE_ETRANGER', "I have a foreigner's card"), ('TITULAIRE_CARTE_SEJOUR_MEMBRE_UE', 'I have a residence card as a family member of an EU citizen.'), ('TITULAIRE_CARTE_SEJOUR_PERMANENT_MEMBRE_UE', 'I have a permanent residence card as a family member of a European Union citizen')], default='', max_length=64, verbose_name='Assimilation 1 situation types')),
                ('long_term_resident_card', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Long-term resident card')),
                ('cire_unlimited_stay_foreigner_card', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='CIRE, unlimited stay or foreigner`s card')),
                ('ue_family_member_residence_card', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Residence card of a family member of a European Union citizen')),
                ('ue_family_member_permanent_residence_card', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Permanent residence card of a family member of a European Union citizen')),
                ('assimilation_2_situation_type', models.CharField(blank=True, choices=[('REFUGIE', 'I am a refugee'), ('DEMANDEUR_ASILE', 'I am an asylum seeker'), ('PROTECTION_SUBSIDIAIRE', 'I benefit from subsidiary protection'), ('PROTECTION_TEMPORAIRE', 'I benefit from temporary protection')], default='', max_length=64, verbose_name='Assimilation 2 situation types')),
                ('refugee_a_b_card', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='A or B card with refugee mention')),
                ('refugees_stateless_annex_25_26', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Annex 25 or 26 for refugees and stateless persons')),
                ('registration_certificate', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Registration certificate')),
                ('a_b_card', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='A or B card')),
                ('subsidiary_protection_decision', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Decision confirming the granting of subsidiary protection')),
                ('temporary_protection_decision', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Decision confirming the granting of temporary protection')),
                ('assimilation_3_situation_type', models.CharField(blank=True, choices=[('AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS', 'I have a residence permit for more than 3 months, and I have a professional income'), ('AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT', 'I have a residence permit for more than 3 months, and I receive a replacement income')], default='', max_length=64, verbose_name='Assimilation 3 situation types')),
                ('professional_3_month_residence_permit', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Residence permit valid for more than 3 months with professional income')),
                ('salary_slips', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Salary slips')),
                ('replacement_3_month_residence_permit', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Residence permit valid for more than 3 months with replacement income')),
                ('unemployment_benefit_pension_compensation_proof', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Proof of receipt of unemployment benefit, pension or compensation')),
                ('cpas_certificate', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Certificate of support from the CPAS')),
                ('relationship', models.CharField(choices=[('PERE', 'My father'), ('MERE', 'My mother'), ('TUTEUR_LEGAL', 'My legal tutor'), ('CONJOINT', 'My partner'), ('COHABITANT_LEGAL', 'My legal cohabitant')], default='', max_length=32, verbose_name='Relationship')),
                ('assimilation_5_situation_type', models.CharField(choices=[('A_NATIONALITE_UE', '<span class="relationship">La personne concernée</span> has the nationality of a country of a Member State of the European Union'), ('TITULAIRE_TITRE_SEJOUR_LONGUE_DUREE', '<span class="relationship">La personne concernée</span> has a long-term residence permit (B, C, D, F, F+ or M cards) in Belgium'), ('CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE', '<span class="relationship">La personne concernée</span> is a refugee applicant, refugee, stateless person, or has temporary/subsidiary protection'), ('AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT', '<span class="relationship">La personne concernée</span> has a residence permit for more than 3 months and receives professional or replacement income'), ('PRIS_EN_CHARGE_OU_DESIGNE_CPAS', '<span class="relationship">La personne concernée</span> is supported by the CPAS, or by a CPAS rest home or designated by the CPAS')], default='', max_length=100, verbose_name='Assimilation 5 situation types')),
                ('household_composition_or_birth_certificate', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Household composition or the birth certificate')),
                ('tutorship_act', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Tutorship act')),
                ('household_composition_or_marriage_certificate', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Household composition or the marriage certificate')),
                ('legal_cohabitation_certificate', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Legal cohabitation certificate')),
                ('parent_identity_card', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Parent identity card')),
                ('parent_long_term_residence_permit', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Parent long-term residence permit')),
                ('parent_refugees_stateless_annex_25_26_or_protection_decision', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Annex 25 or 26 or the A/B card mentioning the refugee status or the decision confirming the protection of the parent')),
                ('parent_3_month_residence_permit', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Parent residence permit valid for more than 3 months')),
                ('parent_salary_slips', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Parent salary slips')),
                ('parent_cpas_certificate', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Parent certificate of support from the CPAS')),
                ('assimilation_6_situation_type', models.CharField(blank=True, choices=[('A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE', 'I benefit from a grant given by the study allowance service of the French Community'), ('A_BOURSE_COOPERATION_DEVELOPPEMENT', 'I benefit from a Development Cooperation grant')], default='', max_length=64, verbose_name='Assimilation 6 situation types')),
                ('cfwb_scholarship_decision', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='CFWB scholarship decision')),
                ('scholarship_certificate', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Scholarship certificate')),
                ('ue_long_term_stay_identity_document', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Identity document proving the long-term stay in a member state of the European Union')),
                ('belgium_residence_permit', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Residence permit in Belgium')),
                ('sport_affiliation', models.CharField(blank=True, choices=[('LOUVAIN_WOLUWE', 'Yes, in Louvain-la-Neuve and/or Woluwe-Saint-Lambert (50 EUR)'), ('MONS_UCL', 'Yes, in Mons and other UCLouvain sites (50 EUR)'), ('MONS', 'Yes, only in Mons (10 EUR)'), ('SAINT_GILLES_UCL', 'Yes, in Saint-Gilles and other UCLouvain sites (50 EUR)'), ('SAINT_GILLES', 'Yes, only in Saint-Gilles (10 EUR)'), ('TOURNAI_UCL', 'Yes, in Tournai and other UCLouvain sites (50 EUR)'), ('TOURNAI', 'Yes, only in Tournai (10 EUR)'), ('NON', 'No')], default='', max_length=32, verbose_name='Sport affiliation')),
                ('solidarity_student', models.BooleanField(blank=True, null=True, verbose_name='Solidarity student')),
                ('account_number_type', models.CharField(blank=True, choices=[('IBAN', 'Yes, an account number in IBAN format'), ('AUTRE_FORMAT', 'Yes, an account number in another format'), ('NON', 'No')], default='', max_length=32, verbose_name='Account number type')),
                ('iban_account_number', models.CharField(blank=True, default='', max_length=34, verbose_name='IBAN account number')),
                ('other_format_account_number', models.CharField(blank=True, default='', max_length=255, verbose_name='Account number')),
                ('bic_swift_code', models.CharField(blank=True, default='', max_length=32, verbose_name='BIC/SWIFT code identifying the bank from which the account was opened')),
                ('account_holder_first_name', models.CharField(blank=True, default='', max_length=128, verbose_name='First name of the account holder')),
                ('account_holder_last_name', models.CharField(blank=True, default='', max_length=128, verbose_name='Last name of the account holder')),
                ('admission', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='accounting', to='admission.doctorateadmission')),
            ],
        ),
    ]
