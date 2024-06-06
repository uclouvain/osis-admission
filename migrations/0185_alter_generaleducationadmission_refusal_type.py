# Generated by Django 3.2.25 on 2024-06-05 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0184_alter_categorizedfreedocument_checklist_tab'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generaleducationadmission',
            name='refusal_type',
            field=models.CharField(
                choices=[
                    ('REFUS_EQUIVALENCE', 'REFUS_EQUIVALENCE'),
                    ('REFUS_BAC_HUE_ACADEMIQUE', 'REFUS_BAC_HUE_ACADEMIQUE'),
                    ('REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIESS', 'REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIESS'),
                    ('REFUS_ARTICLE_95_JURY', 'REFUS_ARTICLE_95_JURY'),
                    ('REFUS_ARTICLE_95_GENERIQUE_IRRECEVABILITE', 'REFUS_ARTICLE_95_GENERIQUE_IRRECEVABILITE'),
                    ('REFUS_AGREGATION', 'REFUS_AGREGATION'),
                    ('REFUS_ARTICLE_96_UE_HUE_ASSIMILES', 'REFUS_ARTICLE_96_UE_HUE_ASSIMILES'),
                    ('REFUS_ARTICLE_96_HUE_RAISON_ACADEMIQUE', 'REFUS_ARTICLE_96_HUE_RAISON_ACADEMIQUE'),
                    ('REFUS_DOSSIER_TARDIF', 'REFUS_DOSSIER_TARDIF'),
                    ('REFUS_COMPLEMENT_TARDIF', 'REFUS_COMPLEMENT_TARDIF'),
                    ('REFUS_ARTICLE_96_HUE_NON_PROGRESSION', 'REFUS_ARTICLE_96_HUE_NON_PROGRESSION'),
                    ('REFUS_LIBRE', 'REFUS_LIBRE'),
                ],
                default='',
                max_length=50,
                verbose_name='Refusal type',
            ),
        ),
    ]
