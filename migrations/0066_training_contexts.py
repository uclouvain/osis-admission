# Generated by Django 3.2.12 on 2022-09-14 11:49

import admission.contrib.models.cdd_config
from django.db import migrations, models
import django.db.models.deletion

from admission.contrib.models.cdd_config import default_category_labels


def forward(apps, schema_editor):
    CddConfiguration = apps.get_model('admission', 'CddConfiguration')
    CddConfiguration.objects.update(category_labels=default_category_labels())


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0632_alter_academiccalendar_reference'),
        ('admission', '0065_accounting'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='context',
            field=models.CharField(choices=[('DOCTORAL_TRAINING', 'DOCTORAL_TRAINING'), ('COMPLEMENTARY_TRAINING', 'COMPLEMENTARY_TRAINING'), ('FREE_COURSE', 'FREE_COURSE')], default='DOCTORAL_TRAINING', max_length=30),
        ),
        migrations.AddField(
            model_name='activity',
            name='course_completed',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AddField(
            model_name='activity',
            name='learning_unit_year',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='base.learningunityear'),
        ),
        migrations.AddField(
            model_name='cddconfiguration',
            name='complementary_course_types',
            field=models.JSONField(default=admission.contrib.models.cdd_config.default_complementary_course_types, verbose_name='COURSE types for complementary training'),
        ),
        migrations.AddField(
            model_name='cddconfiguration',
            name='is_complementary_training_enabled',
            field=models.BooleanField(default=False, help_text='This adds a "Complementary training" tab on admissions concerning this CDD.', verbose_name='Enable complementary training tab'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='category',
            field=models.CharField(choices=[('CONFERENCE', 'CONFERENCE'), ('COMMUNICATION', 'COMMUNICATION'), ('SEMINAR', 'SEMINAR'), ('PUBLICATION', 'PUBLICATION'), ('SERVICE', 'SERVICE'), ('RESIDENCY', 'RESIDENCY'), ('VAE', 'VAE'), ('COURSE', 'COURSE'), ('PAPER', 'PAPER'), ('UCL_COURSE', 'UCL_COURSE')], max_length=50),
        ),
        migrations.AlterModelOptions(
            name='activity',
            options={'ordering': ['-created_at'], 'verbose_name': 'Training activity', 'verbose_name_plural': 'Training activities'},
        ),
        migrations.RunPython(forward, migrations.RunPython.noop)
    ]
