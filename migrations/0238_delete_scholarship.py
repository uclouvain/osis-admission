# Generated by Django 4.2.16 on 2025-01-07 17:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "admission",
            "0237_alter_doctorateadmission_international_scholarship_and_more",
        ),
    ]

    operations = [
        migrations.DeleteModel(
            name="Scholarship",
        ),
    ]
