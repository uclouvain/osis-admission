# Generated by Django 4.2.16 on 2025-01-27 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admission", "0238_merge_20250117_1427"),
    ]

    operations = [
        migrations.AlterField(
            model_name="onlinepayment",
            name="checkout_url",
            field=models.URLField(blank=True, max_length=255),
        ),
    ]