# Generated by Django 3.2.12 on 2022-07-19 15:42

import admission.contrib.models.cdd_config
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0054_config_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='cddconfiguration',
            name='course_types',
            field=admission.contrib.models.cdd_config.TranslatedMultilineField(default=admission.contrib.models.cdd_config.default_course_types, verbose_name='COURSE types'),
        ),
    ]
