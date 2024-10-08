# Generated by Django 3.2.25 on 2024-07-08 15:17

from django.db import migrations
from osis_mail_template import MailTemplateMigration

from admission.mail_templates import ADMISSION_EMAIL_CONFIRM_SUBMISSION_DOCTORATE


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0218_auto_20240828_1051'),
    ]

    operations = [
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRM_SUBMISSION_DOCTORATE,
            {
                'en': '[OSIS] Admission request submitted successfully',
                'fr-be': "[OSIS] Demande d'admission soumise avec succès",
            },
            {
                'en': '''<p>{salutation} {candidate_first_name} {candidate_last_name},</p>

<p>We have received your application for admission, which bears the reference number {admission_reference}.<br>
Provided that your application file is complete, we will evaluate it as soon as possible and keep you informed as our evaluation progresses.<br>
We reserve the right to ask you for additional supporting documents, which must reach us within 15 calendar days of the request. Failure to do so will result in your application not being considered.<br>
Please note that a copy of your application can be downloaded at: {recap_link}.</p>

<p>Thank you for applying to UCLouvain.<br>
Sincerely,<br>
The Enrolment Office and the PhD Subject Committee.</p>
''',
                'fr-be': '''<p>{salutation} {candidate_first_name} {candidate_last_name},</p>

<p>Nous vous confirmons avoir reçu une demande d'admission de votre part qui porte le numéro de référence {admission_reference}.<br>
Pour autant que votre dossier soit complet, nous analyserons votre demande dans les meilleurs délais et ne manquerons pas de vous faire part de son suivi.<br>
Nous nous réservons le droit de vous demander tout justificatif supplémentaire qu'il jugerait utile. Celui-ci devra nous parvenir impérativement dans les 15 jours calendrier qui suivent l'envoi de la demande de justificatif. A défaut, votre demande sera clôturée.</p>

<p>Sachez qu'une copie de votre dossier est téléchargeable à la page suivante : {recap_link}</p>

<p>Nous vous remercions pour la confiance placée dans notre Institution.</p>

<p>Veuillez agréer l'expression de nos salutations distinguées.<br>
Le Service des inscriptions et la Commission doctorale de domaine.</p>
''',
            },
        ),
    ]
