# Generated by Django 3.2.16 on 2022-12-27 16:05

from django.db import migrations
from django.db.models import Value
from django.db.models.functions import Replace

from admission.mail_templates import (
    ADMISSION_EMAIL_CONFIRM_SUBMISSION_CONTINUING,
    ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL,
)
from osis_mail_template import MailTemplateMigration


def replace_in_templates(from_str, to_str):
    def fn(apps, schema_editor):
        MailTemplate = apps.get_model('osis_mail_template', 'MailTemplate')
        MailTemplate.objects.filter(identifier__startswith='admission').update(
            subject=Replace('subject', Value(from_str), Value(to_str)),
            body=Replace('body', Value(from_str), Value(to_str)),
        )

    return fn


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0081_baseadmission_confirmation_elements'),
    ]

    operations = [
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL,
            {
                'en': '[OSIS] Admission request submitted successfully',
                'fr-be': "[OSIS] Demande d'admission soumise avec succès",
            },
            {
                'en': '''<p>Hello {candidate_first_name} {candidate_last_name},</p>
                <p>Your application to {training_title} have been submitted successfully.</p>
                <p>---<br/>
                The OSIS Team</p>
                ''',
                'fr-be': '''<p>Bonjour {candidate_first_name} {candidate_last_name},</p>
                <p>Votre demande d'admission en {training_title} a été soumise avec succès.</p>
                <p>---<br/>
                L'équipe OSIS</p>
                ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRM_SUBMISSION_CONTINUING,
            {
                'en': '[OSIS] Admission request submitted successfully',
                'fr-be': "[OSIS] Demande d'admission soumise avec succès",
            },
            {
                'en': '''<p>Hello {candidate_first_name} {candidate_last_name},</p>
                <p>Your application to {training_title} have been submitted successfully.</p>
                <p>---<br/>
                The OSIS Team</p>
                ''',
                'fr-be': '''<p>Bonjour {candidate_first_name} {candidate_last_name},</p>
                <p>Votre demande d'admission en {training_title} a été soumise avec succès.</p>
                <p>---<br/>
                L'équipe OSIS</p>
                ''',
            },
        ),
        migrations.RunPython(
            replace_in_templates('{doctorate_title}', '{training_title}'),
            reverse_code=replace_in_templates('{training_title}', '{doctorate_title}'),
        ),
    ]
