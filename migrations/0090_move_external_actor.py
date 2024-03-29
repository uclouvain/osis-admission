# Generated by Django 3.2.16 on 2023-01-18 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0089_dates_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='committeemember',
            name='city',
        ),
        migrations.RemoveField(
            model_name='committeemember',
            name='country',
        ),
        migrations.RemoveField(
            model_name='committeemember',
            name='institute',
        ),
        migrations.RemoveField(
            model_name='committeemember',
            name='is_external',
        ),
        migrations.RemoveField(
            model_name='committeemember',
            name='title',
        ),
        migrations.RemoveField(
            model_name='promoter',
            name='city',
        ),
        migrations.RemoveField(
            model_name='promoter',
            name='country',
        ),
        migrations.RemoveField(
            model_name='promoter',
            name='institute',
        ),
        migrations.RemoveField(
            model_name='promoter',
            name='is_external',
        ),
        migrations.RemoveField(
            model_name='promoter',
            name='title',
        ),
        migrations.AlterField(
            model_name='supervisionactor',
            name='type',
            field=models.CharField(choices=[('PROMOTER', 'Supervisor'), ('CA_MEMBER', 'CA Member')], max_length=50),
        ),
        migrations.AddField(
            model_name='supervisionactor',
            name='is_doctor',
            field=models.BooleanField(default=False),
        ),
    ]
