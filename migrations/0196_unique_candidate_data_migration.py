# Generated by Django 3.2.25 on 2024-07-08 17:39
from django.db import migrations

from admission.migrations.utils.remove_duplicates_candidates import remove_duplicate_candidates


def remove_duplicates_candidates_migration(apps, schema_editor):
    remove_duplicate_candidates(apps.get_model('admission', 'Candidate'))


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0195_financabilite_use_base_enum'),
    ]

    operations = [
        migrations.RunPython(remove_duplicates_candidates_migration, reverse_code=migrations.RunPython.noop),
    ]