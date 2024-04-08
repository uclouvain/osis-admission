# Generated by Django 3.2.25 on 2024-03-21 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0169_auto_20240325_1515'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategorizedFreeDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('checklist_tab', models.CharField(blank=True, choices=[('assimilation', 'Belgian student status'), ('financabilite', 'Financeability'), ('frais_dossier', 'Application fee'), ('choix_formation', 'Course choice'), ('parcours_anterieur', 'Previous experience'), ('experiences_parcours_anterieur', 'Previous experiences'), ('donnees_personnelles', 'Personal data'), ('specificites_formation', 'Training specificities'), ('decision_facultaire', 'Decision of the faculty'), ('decision_sic', 'Decision of SIC')], default='', max_length=255)),
                ('short_label_fr', models.CharField(max_length=255, verbose_name='Short label in french')),
                ('short_label_en', models.CharField(blank=True, default='', max_length=255, verbose_name='Short label in english')),
                ('long_label_fr', models.TextField(verbose_name='Long label in french')),
                ('long_label_en', models.TextField(blank=True, verbose_name='Long label in english')),
                ('with_academic_year', models.BooleanField(default=False, verbose_name='With academic year')),
            ],
        ),
    ]