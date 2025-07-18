# Generated by Django 4.2.20 on 2025-04-30 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admission", "0253_promoter_unique_constraint_data_structure"),
    ]

    operations = [
        migrations.AlterField(
            model_name="generaleducationadmission",
            name="refusal_type",
            field=models.CharField(
                choices=[
                    ("REFUS_EQUIVALENCE", "REFUS_EQUIVALENCE"),
                    ("REFUS_BAC_HUE_ACADEMIQUE", "REFUS_BAC_HUE_ACADEMIQUE"),
                    (
                        "REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIEES_MASTER",
                        "REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIEES_MASTER",
                    ),
                    (
                        "REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIEES_MASTER_SPECIALISATION",
                        "REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIEES_MASTER_SPECIALISATION",
                    ),
                    ("REFUS_ARTICLE_95_ACCES_S4", "REFUS_ARTICLE_95_ACCES_S4"),
                    ("REFUS_ARTICLE_95_ACCES_S5", "REFUS_ARTICLE_95_ACCES_S5"),
                    (
                        "REFUS_ARTICLE_95_ACCES_MS_ENSEIGNEMENT",
                        "REFUS_ARTICLE_95_ACCES_MS_ENSEIGNEMENT",
                    ),
                    ("REFUS_ARTICLE_95_JURY", "REFUS_ARTICLE_95_JURY"),
                    (
                        "REFUS_ARTICLE_95_GENERIQUE_IRRECEVABILITE",
                        "REFUS_ARTICLE_95_GENERIQUE_IRRECEVABILITE",
                    ),
                    ("REFUS_AGREGATION", "REFUS_AGREGATION"),
                    (
                        "REFUS_ARTICLE_96_UE_HUE_ASSIMILES",
                        "REFUS_ARTICLE_96_UE_HUE_ASSIMILES",
                    ),
                    (
                        "REFUS_ARTICLE_96_HUE_RAISON_ACADEMIQUE",
                        "REFUS_ARTICLE_96_HUE_RAISON_ACADEMIQUE",
                    ),
                    ("REFUS_DOSSIER_TARDIF", "REFUS_DOSSIER_TARDIF"),
                    ("REFUS_COMPLEMENT_TARDIF", "REFUS_COMPLEMENT_TARDIF"),
                    (
                        "REFUS_ARTICLE_96_HUE_NON_PROGRESSION",
                        "REFUS_ARTICLE_96_HUE_NON_PROGRESSION",
                    ),
                    ("REFUS_LIBRE", "REFUS_LIBRE"),
                ],
                default="",
                max_length=64,
                verbose_name="Refusal type",
            ),
        ),
    ]
