# Generated by Django 3.2.12 on 2023-06-12 12:00

from django.db import migrations

from admission.mail_templates import (
    ADMISSION_EMAIL_SEND_TO_FAC_AT_FAC_DECISION_GENERAL,
)
from osis_mail_template import MailTemplateMigration


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0124_admission_decision_evolutions_2'),
    ]

    OBJECT_TEMPLATE = {
        'en': '[OSIS] A new admission application must be processed ({admission_reference})',
        'fr-be': "[OSIS] Un nouveau dossier d'admission doit être traité ({admission_reference})",
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
                    You will find the analysis folder prepared by the SIC to help you analyze the application, 
                    in the "Documents > "UCLouvain" tab (<a href="{admission_link_back_for_uclouvain_documents}">OSIS
                    </a> application).
                </p>
                
                <p>
                    A user manual for OSIS (Admissions) is available on the website 
                    <a href="https://www.uclouvain.be/fare/">https://www.uclouvain.be/fare/</a> 
                    (Manuals for faculties > Registration / Admission).
                </p>

                <p>
                    Thank you for your cooperation.
                </p>

                <p>
                    The Registration Service.
                </p>        
                
                <p>
                    <a href="mailto:inscription-lln@uclouvain.be">inscription-lln@uclouvain.be</a>
                </p>
                
                ''',
        'fr-be': '''<p>Bonjour,</p>

        <p>
            Le service des inscriptions (SIC) a traité le dossier d'admission de {candidate_last_name}, 
            {candidate_first_name}, <a href="{admission_link_back_for_fac_approval_checklist}">{admission_reference}</a>
             ({candidate_nationality_country}) et a passé le dossier dans la situation "Traitement en Fac".
        </p>

        <p>
            Vous trouverez le dossier d'analyse préparé par SIC afin de vous aider dans l'analyse du dossier, 
            dans l'onglet "Documents > UCLouvain" (Application <a href="{admission_link_back_for_uclouvain_documents}">
            OSIS</a>).
        </p>
        
        <p>
            Un manuel d'utilisation d'OSIS (Admissions) est disponible sur le site 
            <a href="https://www.uclouvain.be/fare/">https://www.uclouvain.be/fare/</a> 
            (Manuels pour les facultés > Inscription / Admission).
        </p>

        <p>
            Nous vous remercions pour votre bonne collaboration.
        </p>

        <p>
            Le service des inscriptions.
        </p>
        
        <p>
            <a href="mailto:inscription-lln@uclouvain.be">inscription-lln@uclouvain.be</a>        
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
