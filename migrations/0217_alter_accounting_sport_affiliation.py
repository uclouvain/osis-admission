# Generated by Django 3.2.25 on 2024-08-23 17:23

from django.db import migrations, models

from admission.ddd.admission.enums import ChoixAffiliationSport


def update_saint_louis_sport_affiliation(apps, schema_editor):
    Accounting = apps.get_model('admission', 'Accounting')
    Accounting.objects.filter(sport_affiliation='SAINT_LOUIS').update(sport_affiliation=ChoixAffiliationSport.NON.name)


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0216_alter_epcinjection_status'),
    ]

    operations = [
        migrations.RunPython(
            code=update_saint_louis_sport_affiliation,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='accounting',
            name='sport_affiliation',
            field=models.CharField(
                blank=True,
                choices=[
                    ('LOUVAIN_WOLUWE', 'Yes, in Louvain-la-Neuve and/or Woluwe-Saint-Lambert (E60)'),
                    ('MONS_UCL', 'Yes, in Mons and other UCLouvain campuses (E60)'),
                    ('MONS', 'Yes, only in Mons (E12)'),
                    ('SAINT_GILLES_UCL', 'Yes, in Saint-Gilles and other UCLouvain campuses (E60)'),
                    ('SAINT_GILLES', 'Yes, only in Saint-Gilles (E12)'),
                    ('TOURNAI_UCL', 'Yes, in Tournai and other UCLouvain campuses (E60)'),
                    ('TOURNAI', 'Yes, only in Tournai (E12)'),
                    ('SAINT_LOUIS_UCL', 'Yes, in Saint-Louis and other UCLouvain campuses (E60)'),
                    ('NON', 'No'),
                ],
                default='',
                max_length=32,
                verbose_name='Sport affiliation',
            ),
        ),
    ]
