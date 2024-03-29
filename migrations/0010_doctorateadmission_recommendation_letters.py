# Generated by Django 2.2.13 on 2021-11-25 11:02

from django.db import migrations, models
import osis_document.contrib.fields


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0009_thesis_language_other'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctorateadmission',
            name='recommendation_letters',
            field=osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Letters of recommendation'),
        ),
    ]
