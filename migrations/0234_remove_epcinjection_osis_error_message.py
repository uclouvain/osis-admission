# Generated by Django 3.2.25 on 2024-10-31 10:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0233_django_4_migration'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='epcinjection',
            name='osis_error_message',
        ),
    ]
