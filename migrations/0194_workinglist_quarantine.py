# Generated by Django 3.2.25 on 2024-06-25 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0193_continuing_update_ways_to_find_out'),
    ]

    operations = [
        migrations.AddField(
            model_name='workinglist',
            name='quarantine',
            field=models.NullBooleanField(),
        ),
    ]