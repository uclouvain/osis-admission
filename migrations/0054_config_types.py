# Generated by Django 3.2.12 on 2022-07-12 20:00

from django.db import migrations

import admission.contrib.models.cdd_config


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0053_confirmation_mail_templates_evolutions'),
    ]

    operations = [
        migrations.AddField(
            model_name='cddconfiguration',
            name='communication_types',
            field=admission.contrib.models.cdd_config.TranslatedMultilineField(default=admission.contrib.models.cdd_config.default_communication_types, verbose_name='COMMUNICATION types'),
        ),
        migrations.AddField(
            model_name='cddconfiguration',
            name='conference_publication_types',
            field=admission.contrib.models.cdd_config.TranslatedMultilineField(default=admission.contrib.models.cdd_config.default_conference_publication_types, verbose_name='CONFERENCE PUBLICATION types'),
        ),
        migrations.AddField(
            model_name='cddconfiguration',
            name='conference_types',
            field=admission.contrib.models.cdd_config.TranslatedMultilineField(default=admission.contrib.models.cdd_config.default_conference_types, verbose_name='CONFERENCE types'),
        ),
        migrations.AddField(
            model_name='cddconfiguration',
            name='publication_types',
            field=admission.contrib.models.cdd_config.TranslatedMultilineField(default=admission.contrib.models.cdd_config.default_publication_types, verbose_name='PUBLICATION types'),
        ),
        migrations.AddField(
            model_name='cddconfiguration',
            name='residency_types',
            field=admission.contrib.models.cdd_config.TranslatedMultilineField(default=admission.contrib.models.cdd_config.default_residency_types, verbose_name='RESIDENCY types'),
        ),
    ]
