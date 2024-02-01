# Generated by Django 3.2.23 on 2023-12-19 09:50

from django.db import migrations, models
import osis_document.contrib.fields


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0136_continuing_education_motivations'),
    ]

    operations = [
        migrations.AddField(
            model_name='generaleducationadmission',
            name='communication_to_the_candidate',
            field=models.TextField(default='', verbose_name='Communication to the candidate'),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='dispensation_needed',
            field=models.CharField(
                choices=[
                    ('NON_CONCERNE', 'NON_CONCERNE'),
                    ('AVIS_DIRECTION_DEMANDE', 'AVIS_DIRECTION_DEMANDE'),
                    ('BESOIN_DE_COMPLEMENT', 'BESOIN_DE_COMPLEMENT'),
                    ('REFUS_DIRECTION', 'REFUS_DIRECTION'),
                    ('ACCORD_DIRECTION', 'ACCORD_DIRECTION'),
                ],
                default='',
                max_length=50,
                verbose_name='Dispensation needed',
            ),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='first_year_inscription_and_status',
            field=models.TextField(blank=True, default='', verbose_name='First year of inscription + status'),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='is_mobility',
            field=models.BooleanField(null=True, verbose_name='The candidate is doing a mobility'),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='mobility_months_amount',
            field=models.CharField(
                choices=[('SIX', '6'), ('DOUZE', '12')],
                default='',
                max_length=50,
                verbose_name='Mobility months amount',
            ),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='must_report_to_sic',
            field=models.BooleanField(blank=True, null=True, verbose_name='The candidate must report to SIC'),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='particular_cost',
            field=models.TextField(blank=True, default='', verbose_name='Particular cost'),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='rebilling_or_third_party_payer',
            field=models.TextField(blank=True, default='', verbose_name='Rebilling or third-party payer'),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='refusal_type',
            field=models.CharField(
                choices=[
                    ('REFUS_EQUIVALENCE', 'REFUS_EQUIVALENCE'),
                    ('REFUS_BAC_HUE_ACADEMIQUE', 'REFUS_BAC_HUE_ACADEMIQUE'),
                    ('REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIESS', 'REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIESS'),
                    ('REFUS_ARTICLE_95_JURY', 'REFUS_ARTICLE_95_JURY'),
                    ('REFUS_AGREGATION', 'REFUS_AGREGATION'),
                    ('REFUS_ARTICLE_96_UE_HUE_ASSIMILES', 'REFUS_ARTICLE_96_UE_HUE_ASSIMILES'),
                    ('REFUS_ARTICLE_96_HUE_RAISON_ACADEMIQUE', 'REFUS_ARTICLE_96_HUE_RAISON_ACADEMIQUE'),
                    ('REFUS_DOSSIER_TARDIF', 'REFUS_DOSSIER_TARDIF'),
                    ('REFUS_COMPLEMENT_TARDIF', 'REFUS_COMPLEMENT_TARDIF'),
                    ('REFUS_ARTICLE_96_HUE_NON_PROGRESSION', 'REFUS_ARTICLE_96_HUE_NON_PROGRESSION'),
                ],
                default='',
                max_length=50,
                verbose_name='Refusal type',
            ),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='sic_annexe_approval_certificate',
            field=osis_document.contrib.fields.FileField(
                base_field=models.UUIDField(),
                blank=True,
                default=list,
                size=None,
                verbose_name='Annexe approval certificate from SIC',
            ),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='sic_approval_certificate',
            field=osis_document.contrib.fields.FileField(
                base_field=models.UUIDField(),
                blank=True,
                default=list,
                size=None,
                verbose_name='Approval certificate from SIC',
            ),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='sic_refusal_certificate',
            field=osis_document.contrib.fields.FileField(
                base_field=models.UUIDField(),
                blank=True,
                default=list,
                size=None,
                verbose_name='Refusal certificate from SIC',
            ),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='tuition_fees_amount',
            field=models.CharField(
                choices=[
                    ('INSCRIPTION_AU_ROLE', 'INSCRIPTION_AU_ROLE'),
                    ('INSCRIPTION_REGULIERE', 'INSCRIPTION_REGULIERE'),
                    ('DROITS_MAJORES', 'DROITS_MAJORES'),
                    ('NOUVEAUX_DROITS_MAJORES', 'NOUVEAUX_DROITS_MAJORES'),
                    ('AGREGATION', 'AGREGATION'),
                    ('MASTER_DE_SPECIALISATION_SANTE', 'MASTER_DE_SPECIALISATION_SANTE'),
                    ('CERTIFICAT_60_CREDITS', 'CERTIFICAT_60_CREDITS'),
                    ('PAS_DE_DROITS_D_INSCRIPTION', 'PAS_DE_DROITS_D_INSCRIPTION'),
                    ('AUTRE', 'AUTRE'),
                ],
                default='',
                max_length=50,
                verbose_name='Tuition fees amount',
            ),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='tuition_fees_amount_other',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Amount (without EUR/)'
            ),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='tuition_fees_dispensation',
            field=models.CharField(
                choices=[
                    ('NON_CONCERNE', 'NON_CONCERNE'),
                    ('DROITS_MAJORES_DEMANDES', 'DROITS_MAJORES_DEMANDES'),
                    ('DISPENSE_LDC', 'DISPENSE_LDC'),
                    ('DISPENSE_REUSSITE', 'DISPENSE_REUSSITE'),
                    ('DISPENSE_BOURSE', 'DISPENSE_BOURSE'),
                    ('DISPENSE_VCRC', 'DISPENSE_VCRC'),
                    ('DISPENSE_OFFRE', 'DISPENSE_OFFRE'),
                    ('DISPENSE_UNIV', 'DISPENSE_UNIV'),
                    ('DISPENSE_DUREE', 'DISPENSE_DUREE'),
                    ('DISPENSE_CESS_FWB', 'DISPENSE_CESS_FWB'),
                    ('REDUCTION_VCRC', 'REDUCTION_VCRC'),
                ],
                default='',
                max_length=50,
                verbose_name='Dispensation or increased fees',
            ),
        ),
    ]
