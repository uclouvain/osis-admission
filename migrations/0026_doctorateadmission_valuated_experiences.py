# Generated by Django 2.2.24 on 2022-02-01 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('osis_profile', '0006_curriculumyear_experience'),
        ('admission', '0025_thesis_language_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctorateadmission',
            name='valuated_experiences',
            field=models.ManyToManyField(
                related_name='valuated_from',
                to='osis_profile.Experience',
                verbose_name='The experiences that have been valuated from this admission.',
            ),
        ),
    ]
