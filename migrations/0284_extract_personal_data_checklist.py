from django.conf import settings
from django.db import migrations

from admission.migrations.utils.extract_personal_data_checklist import extract_personal_data_checklist
from admission.migrations.utils.extract_personal_data_checklist_comment import extract_personal_data_checklist_comment


def extract_personal_data_checklist_migration(apps, schema_editor):
    if settings.TESTING:
        return

    Person = apps.get_model('base', 'Person')

    extract_personal_data_checklist(person_model_class=Person)


def extract_personal_data_checklist_comment_migration(apps, schema_editor):
    if settings.TESTING:
        return

    BaseAdmission = apps.get_model('admission', 'BaseAdmission')
    CommentEntry = apps.get_model('osis_comment', 'CommentEntry')

    extract_personal_data_checklist_comment(comment_model=CommentEntry, base_admission_model=BaseAdmission)


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0283_initialize_iufc_personal_data_checklist'),
        ('base', '0724_person_personal_data_validation'),
        ('osis_comment', '0003_alter_commententry_options'),
    ]

    operations = [
        migrations.RunPython(
            code=extract_personal_data_checklist_migration,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=extract_personal_data_checklist_comment_migration,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
