# Generated by Django 3.2.12 on 2022-07-01 11:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0050_activity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='ects',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=4, verbose_name='ECTS credits'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='end_date',
            field=models.DateField(blank=True, null=True, verbose_name='Activity end date'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='hour_volume',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Total hourly volume'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='participating_days',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True, verbose_name='Number of days participating'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='start_date',
            field=models.DateField(blank=True, null=True, verbose_name='Activity begin date'),
        ),
    ]
