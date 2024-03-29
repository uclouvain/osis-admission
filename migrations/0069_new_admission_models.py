# Generated by Django 3.2.12 on 2022-10-19 16:22

import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0636_alter_academiccalendar_reference'),
        ('osis_profile', '0015_alter_educationalexperience_study_system'),
        ('admission', '0068_scholarship'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctorateadmission',
            name='erasmus_mundus_scholarship',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='+',
                to='admission.scholarship',
                verbose_name='Erasmus Mundus scholarship',
            ),
        ),
        migrations.AlterField(
            model_name='doctorateadmission',
            name='candidate',
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='doctorateadmissions',
                to='base.person',
                verbose_name='Candidate',
            ),
        ),
        migrations.AlterField(
            model_name='doctorateadmission',
            name='educational_valuated_experiences',
            field=models.ManyToManyField(
                related_name='valuated_from_doctorateadmission',
                to='osis_profile.EducationalExperience',
                verbose_name='The educational experiences that have been valuated from this admission.',
            ),
        ),
        migrations.AlterField(
            model_name='doctorateadmission',
            name='professional_valuated_experiences',
            field=models.ManyToManyField(
                related_name='valuated_from_doctorateadmission',
                to='osis_profile.ProfessionalExperience',
                verbose_name='The professional experiences that have been valuated from this admission.',
            ),
        ),
        migrations.CreateModel(
            name='GeneralEducationAdmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('comment', models.TextField(blank=True, default='', verbose_name='Comment')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Modified')),
                (
                    'detailed_status',
                    models.JSONField(default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('CANCELLED', 'CANCELLED'),
                            ('IN_PROGRESS', 'IN_PROGRESS'),
                            ('SUBMITTED', 'SUBMITTED'),
                            ('ENROLLED', 'ENROLLED'),
                        ],
                        default='IN_PROGRESS',
                        max_length=30,
                    ),
                ),
                (
                    'candidate',
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='generaleducationadmissions',
                        to='base.person',
                        verbose_name='Candidate',
                    ),
                ),
                (
                    'double_degree_scholarship',
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='admission.scholarship',
                        verbose_name='Dual degree scholarship',
                    ),
                ),
                (
                    'educational_valuated_experiences',
                    models.ManyToManyField(
                        related_name='valuated_from_generaleducationadmission',
                        to='osis_profile.EducationalExperience',
                        verbose_name='The educational experiences that have been valuated from this admission.',
                    ),
                ),
                (
                    'erasmus_mundus_scholarship',
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='admission.scholarship',
                        verbose_name='Erasmus Mundus scholarship',
                    ),
                ),
                (
                    'international_scholarship',
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='admission.scholarship',
                        verbose_name='International scholarship',
                    ),
                ),
                (
                    'professional_valuated_experiences',
                    models.ManyToManyField(
                        related_name='valuated_from_generaleducationadmission',
                        to='osis_profile.ProfessionalExperience',
                        verbose_name='The professional experiences that have been valuated from this admission.',
                    ),
                ),
                (
                    'training',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='base.educationgroupyear',
                        verbose_name='Course',
                    ),
                ),
            ],
            options={
                'verbose_name': 'General education admission',
                'ordering': ('-created',),
                'permissions': [],
            },
        ),
        migrations.CreateModel(
            name='ContinuingEducationAdmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('comment', models.TextField(blank=True, default='', verbose_name='Comment')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Modified')),
                (
                    'detailed_status',
                    models.JSONField(default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('CANCELLED', 'CANCELLED'),
                            ('IN_PROGRESS', 'IN_PROGRESS'),
                            ('SUBMITTED', 'SUBMITTED'),
                            ('ENROLLED', 'ENROLLED'),
                        ],
                        default='IN_PROGRESS',
                        max_length=30,
                    ),
                ),
                (
                    'candidate',
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='continuingeducationadmissions',
                        to='base.person',
                        verbose_name='Candidate',
                    ),
                ),
                (
                    'educational_valuated_experiences',
                    models.ManyToManyField(
                        related_name='valuated_from_continuingeducationadmission',
                        to='osis_profile.EducationalExperience',
                        verbose_name='The educational experiences that have been valuated from this admission.',
                    ),
                ),
                (
                    'professional_valuated_experiences',
                    models.ManyToManyField(
                        related_name='valuated_from_continuingeducationadmission',
                        to='osis_profile.ProfessionalExperience',
                        verbose_name='The professional experiences that have been valuated from this admission.',
                    ),
                ),
                (
                    'training',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='base.educationgroupyear',
                        verbose_name='Course',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Continuing education admission',
                'ordering': ('-created',),
                'permissions': [],
            },
        ),
        migrations.CreateModel(
            name='ContinuingEducationAdmissionProxy',
            fields=[],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('admission.continuingeducationadmission',),
        ),
        migrations.CreateModel(
            name='GeneralEducationAdmissionProxy',
            fields=[],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('admission.generaleducationadmission',),
        ),
    ]
