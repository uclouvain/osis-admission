# Generated by Django 3.2.23 on 2024-01-25 17:42

from django.db import migrations
from osis_mail_template import MailTemplateMigration

from admission.mail_templates.checklist import (
    ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CHECKERS,
    ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CANDIDATE,
)


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0144_alter_admissiontask_type'),
    ]

    operations = [
        MailTemplateMigration(
            ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CHECKERS,
            {
                'en': "[{candidate_last_name}, {candidate_first_name}, {training_acronym}, {candidate_nationality_country}] "
                "Curriculum verification request",
                'fr-be': "[{candidate_last_name}, {candidate_first_name}, {training_acronym}, {candidate_nationality_country}] "
                "Demande de vérification de cursus",
            },
            {
                'en': '''<p>Dear colleagues,</p>

                <p>                
                    A dossier has been submitted to you to check the authenticity of the diplomas.
                    This is the dossier of {candidate_last_name}, {candidate_first_name}, 
                    <a href="{admission_link_back}" target="_blank">{admission_reference}</a>, 
                    {candidate_nationality_country}.
                    Thank you for your cooperation.
                </p>

                <p>
                    The Enrolment Office
                </p>
                ''',
                'fr-be': '''<p>Cher·ère·s Collègues,</p>
                
                <p>                
                    Un dossier vous est soumis en vérification afin de vérifier l’authenticité des diplômes.
                    Il s'agit du dossier de {candidate_last_name}, {candidate_first_name}, 
                    <a href="{admission_link_back}" target="_blank">{admission_reference}</a>, 
                    {candidate_nationality_country}.
                    Nous vous remercions pour votre bonne collaboration.
                </p>
    
                <p>
                    Le service des inscriptions
                </p>
                ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CANDIDATE,
            {
                'en': "[{candidate_last_name}, {candidate_first_name}, {admission_reference}] "
                "Authentication in progress - UCLouvain",
                'fr-be': "[{candidate_last_name}, {candidate_first_name}, {admission_reference}] "
                "Dossier en cours d'authentification - UCLouvain",
            },
            {
                'en': '''<p>Dear Sir/Madam,</p>

                <p>
                    As part of your application for admission to the {training_title} ({training_campus}) - 
                    {training_acronym} programme and as specified in the online application you completed, we are 
                    authenticating your previous academic record.
                </p>
                
                <p>
                    Without a response from the various institutions you have attended, we will not be able to proceed 
                    with your application.
                </p>     
                           
               <p>
                   We are working hard to obtain authentication of your background as soon as possible.
               </p>
               
               <p>
                   However, further analysis of your application and responding to your application for admission are 
                   now dependent on the responsiveness of your previous educational institutions.
               </p>

                <p>
                    We thank you for your understanding.
                </p>
                
                <p>
                    The Enrolment Office
                </p>
                ''',
                'fr-be': '''<p>Madame, Monsieur,</p>
                
                <p>
                    Dans le cadre de votre demande d’admission pour le programme {training_title} ({training_campus}) - 
                    {training_acronym} et comme précisé dans la demande en ligne que vous avez complétée, nous 
                    procédons à une authentification de votre parcours académique antérieur.
                </p>
                
                <p>
                    Sans réponse de la part des différents établissements que vous avez fréquentés, il ne nous sera 
                    pas possible de donner suite à votre demande d’admission.
                </p>     
                           
               <p>
                    Nous nous mobilisons pour obtenir l’authentification de votre parcours dans les meilleurs délais.
               </p>
                
               <p>
                  Cependant, la suite de l’analyse de votre dossier et le délai de réponse à votre demande d’admission 
                  sont maintenant tributaires de la réactivité de vos établissements d’enseignement antérieurs.
               </p>

                <p>
                    Nous vous remercions de votre compréhension.
                </p>
                
                <p>
                    Le Service des inscriptions
                </p>
                ''',
            },
        ),
    ]