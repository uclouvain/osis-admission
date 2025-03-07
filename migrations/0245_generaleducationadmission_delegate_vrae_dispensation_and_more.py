# Generated by Django 4.2.16 on 2025-03-06 14:29

import osis_document.contrib.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "admission",
            "0244_remove_doctorateadmission_program_planned_years_number_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="generaleducationadmission",
            name="delegate_vrae_dispensation",
            field=models.CharField(
                blank=True,
                choices=[
                    ("DEROGATION_DELEGUE", "DEROGATION_DELEGUE"),
                    ("DEROGATION_VRAE", "DEROGATION_VRAE"),
                    ("PAS_DE_DEROGATION", "PAS_DE_DEROGATION"),
                ],
                default="",
                max_length=50,
                verbose_name="Delegate VRAE dispensation",
            ),
        ),
        migrations.AddField(
            model_name="generaleducationadmission",
            name="delegate_vrae_dispensation_certificate",
            field=osis_document.contrib.fields.FileField(
                base_field=models.UUIDField(),
                blank=True,
                default=list,
                size=None,
                verbose_name="Delegate VRAE dispensation certificate",
            ),
        ),
        migrations.AddField(
            model_name="generaleducationadmission",
            name="delegate_vrae_dispensation_comment",
            field=models.TextField(
                blank=True,
                default="",
                verbose_name="Delegate VRAE dispensation comment",
            ),
        ),
        migrations.AlterField(
            model_name="generaleducationadmission",
            name="dispensation_needed",
            field=models.CharField(
                choices=[
                    ("NON_CONCERNE", "NON_CONCERNE"),
                    ("AVIS_DIRECTION_DEMANDE", "AVIS_DIRECTION_DEMANDE"),
                    ("BESOIN_DE_COMPLEMENT", "BESOIN_DE_COMPLEMENT"),
                    ("REFUS_DIRECTION", "REFUS_DIRECTION"),
                    ("ACCORD_DIRECTION", "ACCORD_DIRECTION"),
                ],
                default="",
                max_length=50,
                verbose_name="Non-progression dispensation needed",
            ),
        ),
    ]
