# Generated by Django 4.2.16 on 2025-02-26 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admission", "0245_alter_accounting_sport_affiliation"),
    ]

    operations = [
        migrations.AddField(
            model_name="doctorateadmission",
            name="approved_by_cdd_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Approved by CDD at"),
        ),
    ]
