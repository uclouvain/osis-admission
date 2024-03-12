# Generated by Django 3.2.24 on 2024-02-23 17:37

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('osis_profile', '0025_alter_educationalexperienceyear_external_id'),
        ('admission', '0158_auto_20240228_0919'),
    ]

    operations = [
        migrations.CreateModel(
            name='FreeAdditionalApprovalCondition',
            fields=[
                (
                    'uuid',
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ('name_fr', models.TextField(blank=True, default='', verbose_name='French name',)),
                ('name_en', models.TextField(blank=True, default='', verbose_name='English name',)),
                (
                    'admission',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='admission.generaleducationadmission',
                        verbose_name='Admission',
                    ),
                ),
                (
                    'related_experience',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to='osis_profile.educationalexperience',
                        to_field='uuid',
                        verbose_name='Related experience',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Free additional approval condition',
                'verbose_name_plural': 'Free additional approval conditions',
            },
        ),
    ]
