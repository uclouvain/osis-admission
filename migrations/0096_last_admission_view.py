# Generated by Django 3.2.17 on 2023-03-14 11:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0647_merge_20230113_1039'),
        ('admission', '0095_new_admission_statuses'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdmissionViewer',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'viewed_at',
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name='Viewed at',
                    ),
                ),
                (
                    'admission',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='admission.baseadmission',
                        verbose_name='Admission',
                    ),
                ),
                (
                    'person',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='base.person',
                        verbose_name='Person',
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name='baseadmission',
            name='viewers',
            field=models.ManyToManyField(
                related_name='viewed_admissions',
                through='admission.AdmissionViewer',
                to='base.Person',
                verbose_name='Viewed by',
            ),
        ),
    ]
