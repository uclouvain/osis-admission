# Generated by Django 2.2.13 on 2021-10-27 14:18

from django.db import migrations, models
import osis_document.contrib.fields


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0002_auto_20211014_1433'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctorateadmission',
            name='cotutelle_convention',
            field=osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=1,
                                                         verbose_name="Joint supervision agreement"),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='cotutelle_institution',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Institution'),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='cotutelle_motivation',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Motivation'),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='cotutelle_opening_request',
            field=osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=1,
                                                         verbose_name='Cotutelle request document'),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='cotutelle_other_documents',
            field=osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None,
                                                         verbose_name="Other cotutelle-related documents"),
        ),
    ]
