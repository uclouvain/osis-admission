# Generated by Django 3.2.12 on 2022-05-30 15:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0047_confirmation_paper_evolutions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admissiontask',
            name='type',
            field=models.CharField(
                choices=[
                    ('ARCHIVE', 'PDF Export'),
                    ('CANVAS', 'Canvas'),
                    ('CONFIRMATION_SUCCESS', 'Confirmation success attestation'),
                ],
                max_length=20,
            ),
        ),
    ]
