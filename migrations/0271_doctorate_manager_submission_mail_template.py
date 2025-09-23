from django.db import migrations
from osis_mail_template import MailTemplateMigration

from admission.mail_templates import (
    ADMISSION_EMAIL_CONFIRM_SUBMISSION_FOR_MANAGER_DOCTORATE,
)


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0270_mail_template_signatures'),
    ]

    operations = [
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRM_SUBMISSION_FOR_MANAGER_DOCTORATE,
            {
                'en': '[OSIS] Admission request submitted',
                'fr-be': '[OSIS] Dossier d\'admission soumis',
            },
            {
                'en': '''<p>Hello {manager_first_name} {manager_last_name},</p>

<p>{candidate_first_name} {candidate_last_name} has submitted his admission request to the CDD.</p>

<p>Here is the link to its admission request <a href="{admission_link_back}">{admission_link_back}</a>.</p>

''',
                'fr-be': '''<p>Bonjour {manager_first_name} {manager_last_name},</p>

<p>{candidate_first_name} {candidate_last_name} a soumis son dossier en CDD.</p>

<p>Voici le lien vers son dossier <a href="{admission_link_back}">{admission_link_back}</a>.</p>
''',
            },
        ),
    ]
