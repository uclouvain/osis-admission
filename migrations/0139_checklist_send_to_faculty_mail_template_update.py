from django.db import migrations

from admission.mail_templates import (
    ADMISSION_EMAIL_SEND_TO_FAC_AT_FAC_DECISION_GENERAL,
)
from osis_mail_template import MailTemplateMigration


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0138_alter_email_confirm_continuing_submission'),
    ]

    OBJECT_TEMPLATE = {
        'en': 'OSIS [{candidate_last_name}, {candidate_first_name}, {training_acronym}] Application submitted to the '
        'faculty',
        'fr-be': "OSIS [{candidate_last_name}, {candidate_first_name}, {training_acronym}] Demande d'inscription "
        "soumise en faculté",
    }

    CONTENT_TEMPLATE = {
        'en': '''<p>Hello</p>

                <p>
                    The Registration Service (SIC) has processed the application of {candidate_last_name}, 
                    {candidate_first_name}, <a href="{admission_link_back_for_fac_approval_checklist}">
                    {admission_reference}</a> ({candidate_nationality_country}) and has changed the 
                    status of the application to "Processing by Fac".
                </p>

                <p>
                    A user manual for OSIS (Registration requests) is available on the website 
                    <a href="https://www.uclouvain.be/fare">https://www.uclouvain.be/fare</a> 
                    (Manuals for faculties > Registration/Admission).
                </p>

                <p>
                    Thank you for your cooperation.
                </p>

                <p>
                    The Registration Service.
                </p>        
                
                <p>
                    <a href="mailto:{training_enrollment_campus_email}">{training_enrollment_campus_email}</a>
                </p>
                
                ''',
        'fr-be': '''<p>Bonjour,</p>

        <p>
            Le service des inscriptions (SIC) a traité le dossier d'admission de {candidate_last_name}, 
            {candidate_first_name}, <a href="{admission_link_back_for_fac_approval_checklist}">{admission_reference}</a>
             ({candidate_nationality_country}) et a passé le dossier dans la situation "Traitement en Fac".
        </p>

        <p>
            Un manuel d'utilisation d'OSIS (Demandes d'inscriptions) est disponible sur le site 
            <a href="https://www.uclouvain.be/fare">https://www.uclouvain.be/fare</a> 
            (Manuels pour les facultés > Inscription/Admission).
        </p>

        <p>
            Nous vous remercions pour votre bonne collaboration.
        </p>

        <p>
            Le service des inscriptions.
        </p>
        
        <p>
            <a href="mailto:{training_enrollment_campus_email}">{training_enrollment_campus_email}</a>
        </p>
        ''',
    }

    operations = [
        MailTemplateMigration(
            ADMISSION_EMAIL_SEND_TO_FAC_AT_FAC_DECISION_GENERAL,
            OBJECT_TEMPLATE,
            CONTENT_TEMPLATE,
        ),
    ]
