# Generated by Django 3.2.23 on 2024-02-13 15:56

from django.db import migrations

from admission.migrations.utils.initialize_past_experiences_checklist import (
    initialization_of_missing_checklists_in_cv_experiences,
)


def initialization_migration_of_missing_checklists_in_cv_experiences(apps, schema_editor):
    initialization_of_missing_checklists_in_cv_experiences(apps.get_model('admission', 'BaseAdmission'))


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0162_workinglist'),
    ]

    operations = [
        migrations.RunPython(
            code=initialization_migration_of_missing_checklists_in_cv_experiences,
            reverse_code=migrations.RunPython.noop,
        ),
    ]