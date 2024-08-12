# Generated by Django 3.2.25 on 2024-08-01 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0211_auto_20240731_1011'),
    ]

    operations = [
        migrations.AlterField(
            model_name='epcinjection',
            name='status',
            field=models.CharField(blank=True, choices=[('OK', 'Injecté'), ('ERROR', 'Erreur'), ('PENDING', "En attente du retour d'EPC")], default='', max_length=7),
        ),
    ]
