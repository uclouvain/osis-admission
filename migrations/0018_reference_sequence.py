# Generated by Django 2.2.13 on 2022-01-07 11:35

from django.db import migrations
from django.db.backends.postgresql.schema import DatabaseSchemaEditor

from admission.models.base import REFERENCE_SEQ_NAME


def create_reference_sequence(apps, schema_editor: DatabaseSchemaEditor):
    DoctorateAdmission = apps.get_model('admission', 'DoctorateAdmission')
    cursor = schema_editor.connection.cursor()
    cursor.execute(schema_editor.sql_create_sequence % {'sequence': REFERENCE_SEQ_NAME})
    cursor.execute(schema_editor.sql_set_sequence_max % {
        'sequence': REFERENCE_SEQ_NAME,
        "table": DoctorateAdmission._meta.db_table,
        "column": 'id',
    })


def drop_reference_sequence(apps, schema_editor: DatabaseSchemaEditor):
    cursor = schema_editor.connection.cursor()
    cursor.execute(schema_editor.sql_delete_sequence % {'sequence': REFERENCE_SEQ_NAME})


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0017_simpler_roles'),
    ]

    operations = [
        migrations.RunPython(create_reference_sequence, drop_reference_sequence),
    ]
