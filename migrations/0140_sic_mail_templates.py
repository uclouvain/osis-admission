# Generated by Django 3.2.23 on 2024-01-19 09:10

from django.db import migrations
from osis_mail_template import MailTemplateMigration

from admission.mail_templates.checklist import ADMISSION_EMAIL_SIC_REFUSAL, ADMISSION_EMAIL_SIC_APPROVAL


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0139_checklist_send_to_faculty_mail_template_update'),
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
        
        <p>Vous trouverez les motifs de cette décision dans le document ci-joint.</p>
        
        <p>Veuillez agréer, Madame, Monsieur, l'expression de nos salutations distinguées.</p>
        
        <p>Virginie Odeurs<br>
        Directrice du Service des inscriptions</p>
                ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_SIC_APPROVAL,
            {
                'en': 'Enrolment authorisation ({admission_reference})',
                'fr-be': "Autorisation d'inscription suite à une demande d'admission ({admission_reference})",
            },
            {
                'en': '''<p>Dear {candidate}</p>

            <p>We are pleased to inform you that you are authorised to enrol in the {admission_training}
             for the {academic_year} academic year.</p>
            
            <p>If you require a student visa, please use the attached enrolment authorisation and visa application to 
              apply via your local Belgian embassy or consulate. For more information, 
              consult the <a href="https://dofi.ibz.be/en">Belgian Immigration Office</a>.</p>
            
            <p>After you have obtained your visa, please send us the signed enrolment authorisation and any
              additional documents to <a href="mailto:{admission_email}">{admission_email}</a>.
              These documents are required to finalise your enrolment.</p>
            
            <p>For enrolment questions, please see <a href="https://uclouvain.be/en/study/inscriptions">our website</a>
              .</p>
            
            <p>The <a href="https://uclouvain.be/en/study/academic-calendar-1.html">academic year</a>
              begins on {academic_year_start_date}.</p>
            
            <p>For questions concerning your arrival in Belgium, please see
              <a href="https://uclouvain.be/en/study/inscriptions/welcome-to-international-students.html">
              our international students webpage</a>.</p>
            
            <p>Welcome to UCLouvain.</p>
            
            <p>Sincerely,<br>
            The Enrolment Office</p>
            ''',
                'fr-be': '''<p>{greetings} {candidate},</p>

            <p>Nous avons le plaisir de vous informer que vous êtes autorisé·e à vous inscrire au programme
              {admission_training} pour l'année académique {academic_year}.</p>
            
            <p>Vous trouverez ci-joint votre autorisation d'inscription qui comprend toutes les informations utiles 
              et les éventuelles conditions à remplir préalablement à votre inscription.</p>
            
            <p>Si vous êtes concerné·e par l'obtention d'un visa d'études, l'autorisation d'inscription accompagnée 
              du formulaire pour la demande de visa (documents en annexe) vous permettent d'entamer ces démarches
              auprès de l'ambassade ou du consulat de Belgique local·e. Nous vous invitons à consulter le
              <a href="https://dofi.ibz.be/fr">site officiel de l'Office des étrangers</a>.</p>
            
            <p>Afin de finaliser votre inscription à l'Université, nous vous remercions de nous transmettre
              l'autorisation signée ainsi que les éventuels documents complémentaires à l'adresse
              <a href="mailto:{admission_email}">{admission_email}</a>. Nous vous rappelons qu'il est impératif de 
              nous renvoyer ces documents après l'obtention de votre visa.</p>
            
            <p>Pour toute question relative à l'inscription, nous vous invitons à consulter
              <a href="https://uclouvain.be/fr/etudier/inscriptions">notre site</a>.</p>
            
            <p>Nous vous informons que le début de l'année académique est fixé au {academic_year_start_date}
              <a href="https://uclouvain.be/fr/etudier/calendrier-academique.html">(Calendrier académique)</a>.</p>
            
            <p>Si vous avez des questions concernant votre arrivée en Belgique, vous avez à votre disposition
              toute une série d'informations sur
              <a href="https://uclouvain.be/fr/etudier/inscriptions/bienvenue-aux-etudiants-internationaux-et-aux-etudiantes-internationales.html">
              notre page</a>.</p>
            
            <p>Nous vous souhaitons la bienvenue à l'UCLouvain.</p>
            
            <p>Veuillez agréer l'expression de nos salutations distinguées.<br>
            Le Service des inscriptions</p>
            ''',
            },
        ),
    ]