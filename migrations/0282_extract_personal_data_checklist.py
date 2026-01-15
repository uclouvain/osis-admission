from django.conf import settings
from django.db import migrations

from admission.migrations.utils.extract_personal_data_checklist import (
    extract_personal_data_checklist,
)


def extract_personal_data_checklist_migration(apps, schema_editor):
    if settings.TESTING:
        return

    Person = apps.get_model('base', 'Person')

    extract_personal_data_checklist(person_model_class=Person)


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0281_initialize_iufc_personal_data_checklist'),
        ('base', '0723_person_personal_data_validation'),
    ]

    operations = [
        migrations.RunPython(
            code=extract_personal_data_checklist_migration,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
