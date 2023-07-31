# Generated by Django 3.2.19 on 2023-07-04 16:28

from django.db import migrations, models
from django.db.models import Case, When, Value, F

from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale

GENERAL_MAPPING_STATUS = {
    'A_COMPLETER_POUR_FAC_CDD': ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
    'TRAITEMENT_SIC': ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name,
    'TRAITEMENT_FAC_CDD': ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name,
}


def forward(apps, schema_editor):
    # Update statuses
    GeneralEducationAdmission = apps.get_model("admission", "GeneralEducationAdmission")
    cases = [
        When(status=old_status, then=Value(new_status)) for old_status, new_status in GENERAL_MAPPING_STATUS.items()
    ]
    GeneralEducationAdmission.objects.update(status=Case(*cases, default=F('status')))


def backward(apps, schema_editor):
    # Update statuses
    GeneralEducationAdmission = apps.get_model("admission", "GeneralEducationAdmission")
    cases = [
        When(status=new_status, then=Value(old_status)) for old_status, new_status in GENERAL_MAPPING_STATUS.items()
    ]
    GeneralEducationAdmission.objects.update(status=Case(*cases, default=F('status')))


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0108_alter_generaleducationadmission_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='baseadmission',
            name='fac_documents',
        ),
        migrations.RemoveField(
            model_name='baseadmission',
            name='sic_documents',
        ),
        migrations.AlterField(
            model_name='generaleducationadmission',
            name='status',
            field=models.CharField(
                choices=[
                    ('EN_BROUILLON', 'In draft'),
                    ('FRAIS_DOSSIER_EN_ATTENTE', 'Pending application fees'),
                    ('CONFIRMEE', 'Confirmed application (by student)'),
                    ('ANNULEE', 'Cancelled application'),
                    ('A_COMPLETER_POUR_SIC', 'To be completed (by student) for SIC'),
                    ('COMPLETEE_POUR_SIC', 'Completed (by student) for SIC'),
                    ('TRAITEMENT_FAC', 'Processing by Fac/CDD'),
                    ('A_COMPLETER_POUR_FAC', 'To be completed (by student) for FAC'),
                    ('COMPLETEE_POUR_FAC', 'Completed (by student) for FAC'),
                    ('RETOUR_DE_FAC', 'Feedback from FAC'),
                    ('ATTENTE_VALIDATION_DIRECTION', 'Pending validation from management'),
                    ('INSCRIPTION_AUTORISEE', 'Enrollment allowed'),
                    ('INSCRIPTION_REFUSEE', 'Enrollment denied'),
                    ('CLOTUREE', 'Closed'),
                ],
                default='EN_BROUILLON',
                max_length=30,
            ),
        ),
        migrations.RunPython(code=forward, reverse_code=backward),
    ]
