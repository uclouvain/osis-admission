# Generated by Django 3.2.18 on 2023-04-19 17:48

import django.core.serializers.json
from django.db import migrations, models
import osis_document.contrib.fields


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0100_submitted_profile_to_baseadmission'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseadmission',
            name='fac_documents',
            field=osis_document.contrib.fields.FileField(base_field=models.UUIDField(), blank=True, default=list, size=None, verbose_name='FAC free documents'),
        ),
        migrations.AddField(
            model_name='baseadmission',
            name='requested_documents',
            field=models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder, verbose_name='Requested documents'),
        ),
        migrations.AddField(
            model_name='baseadmission',
            name='sic_documents',
            field=osis_document.contrib.fields.FileField(base_field=models.UUIDField(), blank=True, default=list, size=None, verbose_name='SIC free documents'),
        ),
        migrations.AddField(
            model_name='baseadmission',
            name='uclouvain_fac_documents',
            field=osis_document.contrib.fields.FileField(base_field=models.UUIDField(), blank=True, default=list, size=None, verbose_name='UCLouvain FAC free documents'),
        ),
        migrations.AddField(
            model_name='baseadmission',
            name='uclouvain_sic_documents',
            field=osis_document.contrib.fields.FileField(base_field=models.UUIDField(), blank=True, default=list, size=None, verbose_name='UCLouvain SIC free documents'),
        ),
    ]
