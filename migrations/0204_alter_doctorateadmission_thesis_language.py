# Generated by Django 3.2.25 on 2024-07-10 16:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reference', '0018_country_active'),
        ('admission', '0203_auto_20240712_1536'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='doctorateadmission',
            name='thesis_language',
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='thesis_language',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='reference.language',
                verbose_name='Thesis language',
            ),
        ),
    ]
