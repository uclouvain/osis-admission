# Generated by Django 2.2.13 on 2021-10-14 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctorateadmission',
            name='phd_already_done',
            field=models.CharField(blank=True, choices=[('YES', 'YES'), ('NO', 'NO'), ('PARTIAL', 'PARTIAL')], default='NO', max_length=255, verbose_name='PhD already done'),
        ),
    ]
