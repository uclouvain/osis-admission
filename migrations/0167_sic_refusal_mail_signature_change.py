# Generated by Django 3.2.23 on 2024-02-15 14:33

from django.db import migrations
from osis_mail_template import MailTemplateMigration

from admission.mail_templates.checklist import ADMISSION_EMAIL_SIC_REFUSAL


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0166_sic_refusal_mail_director_gender'),
    ]

    operations = [
        MailTemplateMigration(
            ADMISSION_EMAIL_SIC_REFUSAL,
            {
                'en': '',
                'fr-be': "UCLouvain - suivi de votre demande d'inscription - {admission_reference}",
            },
            {
                'en': '',
                'fr-be': '''<p>A l'attention de {candidate},</p>

                <p>Votre demande d'inscription à l'année académique {academic_year} au programme {admission_training}
                  nous est bien parvenue et nous vous en remercions.</p>

                <p>Après analyse de votre dossier, nous sommes au regret de vous informer que votre demande d'inscription n'a
                  pu faire l'objet d'une réponse favorable.</p>

                <p>Pour prendre connaissances des motifs, <strong>nous vous invitons à télécharger
                <a href="{document_link}">votre courrier d’irrecevabilité</a>
                et à le conserver</strong>. Ce lien sera valide pendant 1 an à dater de ce jour.</p>

                <p>Veuillez agréer, Madame, Monsieur, l'expression de nos salutations distinguées.</p>

                <p>Le Service des inscriptions</p>
                ''',
            },
        ),
    ]
