# Generated by Django 2.2.13 on 2021-11-17 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0006_doctorateadmission_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctorateadmission',
            name='cotutelle',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
