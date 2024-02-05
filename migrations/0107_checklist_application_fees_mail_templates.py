# Generated by Django 3.2.12 on 2023-06-12 12:00

from django.db import migrations

from admission.mail_templates import (
    ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL,
)
from osis_mail_template import MailTemplateMigration


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0106_alter_activity_ects'),
    ]

    OBJECT_TEMPLATE = {
        'en': '[OSIS] Payment of your application fee ({admission_reference})',
        'fr-be': "[OSIS] Paiement de vos frais de dossier ({admission_reference})",
    }

    CONTENT_TEMPLATE = {
        'en': '''<p>Dear Madam or Sir</p>

                <p>
                    The Registration Service of the Université catholique de Louvain confirms that it has received 
                    an admission request from you, bearing the reference: {admission_reference}.
                </p>

                <p>
                    After an initial analysis of your file, we note that you are not exempt from the application fee.
                    We invite you to pay these by going to the following page: <a href="{admissions_link_front}">
                    {admissions_link_front}</a>.
                </p>

                <p>
                    The application fee must be received <strong>within 15 calendar days</strong>.
                    Failure to do so will result in your application being closed.
                </p>

                <p>
                    Once payment has been made and received in our account, we will analyse your application as soon 
                    as possible and let you know how it is progressing.
                </p>
                
                <p>
                    The Enrolment Department reserves the right to ask you for any additional proof it deems necessary. 
                    This must reach us <strong>within 15 calendar days</strong>. Failure to do so will result in your application 
                    being closed.
                </p>
                
                <p>
                    A copy of your application can be downloaded from the following page: <a href="{admissions_link_front}">
                    {admissions_link_front}</a>.
                </p>

                <p>
                    Thank you for your confidence in our institution.
                </p>

                <p>
                    The UCLouvain Registration Service.
                </p>        ''',
        'fr-be': '''<p>Madame, Monsieur,</p>

        <p>
            Le Service des inscriptions de l'Université catholique de Louvain vous confirme avoir reçu une demande 
            d'admission de votre part qui porte le numéro de référence : {admission_reference}.
        </p>

        <p>
            Après une première analyse de votre dossier, nous constatons que vous n'êtes pas exonéré·e des frais de 
            dossier. Nous vous invitons à réaliser le payement de ceux-ci en vous rendant sur la page suivante : 
            <a href="{admissions_link_front}">{admissions_link_front}</a>.
        </p>

        <p>
            Le montant des frais de dossier devra nous parvenir <strong>impérativement dans les 15 jours 
            calendrier </strong>. A défaut, votre demande sera clôturée.
        </p>

        <p>
            Une fois le payement effectué et réceptionné sur notre compte, nous analyserons votre demande dans les 
            meilleurs délais et ne manquerons pas de vous faire part de son suivi.
        </p>
        
        <p>
            Le Service des inscriptions se réserve le droit de vous demander tout justificatif supplémentaire qu'il 
            jugerait utile. Celui-ci devra nous parvenir <strong>impérativement dans les 15 jours calendrier</strong>. 
            A défaut, votre demande sera clôturée.
        </p>
        
        <p>
            Sachez qu'une copie de votre dossier est téléchargeable à la page suivante : 
            <a href="{admissions_link_front}">{admissions_link_front}</a>.
        </p>

        <p>
            Nous vous remercions pour la confiance placée dans notre Institution.
        </p>

        <p>
            Le Service des inscriptions de l'UCLouvain.
        </p>
        ''',
    }

    operations = [
        MailTemplateMigration(
            ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL,
            OBJECT_TEMPLATE,
            CONTENT_TEMPLATE,
        ),
    ]
