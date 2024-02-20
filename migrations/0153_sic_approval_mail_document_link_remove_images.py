from django.db import migrations
from osis_mail_template import MailTemplateMigration

from admission.mail_templates.checklist import ADMISSION_EMAIL_SIC_APPROVAL


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0152_sic_approval_mail_document_link'),
    ]

    operations = [
        MailTemplateMigration(
            ADMISSION_EMAIL_SIC_APPROVAL,
            {
                'en': 'Enrolment authorisation ({admission_reference})',
                'fr-be': "Autorisation d'inscription suite à une demande d'admission ({admission_reference})",
            },
            {
                'en': '''<p>{greetings} {candidate_first_name} {candidate_last_name},</p>
            <br>

            <p>
                We are pleased to inform you that you are authorised to enrol in the {training_title} 
                ({training_campus}) - {training_acronym} for the {academic_year} academic year.
            </p>

            <p>
                Please download your enrolment authorisation which contains all the relevant information and any 
                conditions that need to be met before registering.
            </p>

            <p style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                <span style="color: #dc3545; border: 1px solid #dc3545; padding: 10px; border-radius: 10px;">
                    Download: 
                    <a
                        href="{enrollment_authorization_document_link}"
                        target="_blank"
                        style="color: #dc3545;"
                    >Enrolment authorisation</a>
                </span>
            </p>

            <p>
                If you require a student visa, please use the enrolment authorisation and the visa application to 
                apply via your local Belgian embassy or consulate. For more information, 
                consult the <a href="https://dofi.ibz.be/en" target="_blank" style="color: #0000EE;">Belgian Immigration Office</a>.
            </p>
            
            <p style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                <span style="color: #dc3545; border: 1px solid #dc3545; padding: 10px; border-radius: 10px;">
                    Download: 
                    <a
                        href="{visa_application_document_link}"
                        target="_blank"
                        style="color: #dc3545;"
                    >Visa application</a>
                </span>
            </p>

            <p>
                After you have obtained your visa, please send us the signed enrolment authorisation and any 
                additional documents to the email address below. These documents are required to finalise your 
                enrolment.
            </p>

            <p style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                <span style="color: #0000EE; border: 1px solid #0000EE; padding: 10px; border-radius: 10px;">
                    Send to: 
                    <a href="mailto:{admission_email}" target="_blank" style="color: #0000EE;">{admission_email}</a>
                </span>
            </p>

            <p>
                For enrolment questions, please see 
                <a href="https://uclouvain.be/en/study/inscriptions" target="_blank" style="color: #0000EE;">our website</a>.
            </p>

            <p>
                The <a href="https://uclouvain.be/en/study/academic-calendar-1.html" target="_blank" style="color: #0000EE;">academic year</a> 
                begins on {academic_year_start_date}.
            </p>

            <p>
                For questions concerning your arrival in Belgium, please see 
                <a href="https://uclouvain.be/en/study/inscriptions/welcome-to-international-students.html" target="_blank" style="color: #0000EE;">
                our international students webpage</a>.
            </p>

            <p>
                Welcome to UCLouvain.
            </p>
            <br>

            <p>
                Sincerely,
            </p>

            <p>
                The Enrolment Office
            </p>
            ''',
                'fr-be': '''<p>{greetings} {candidate_first_name} {candidate_last_name},</p>
            <br>

            <p>
                Nous avons le plaisir de vous informer que vous êtes autorisé·e à vous inscrire au programme 
                {training_title} ({training_campus}) - {training_acronym} pour l'année académique {academic_year}.
            </p>

            <p>
                Veuillez télécharger votre autorisation d'inscription qui comprend toutes les informations utiles et 
                les éventuelles conditions à remplir préalablement à votre inscription.
            </p>

            <p style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                <span style="color: #dc3545; border: 1px solid #dc3545; padding: 10px; border-radius: 10px;">
                    Télécharger : 
                    <a
                        href="{enrollment_authorization_document_link}"
                        target="_blank"
                        style="color: #dc3545;"
                    >Autorisation d'inscription</a>
                </span>
            </p>

            <p>
                Si vous êtes concerné·e par l'obtention d'un visa d'études, l'autorisation d'inscription accompagnée du 
                formulaire pour la demande de visa vous permettent d'entamer ces démarches auprès de l'ambassade ou du 
                consulat de Belgique local·e. Nous vous invitons à consulter le 
                <a href="https://dofi.ibz.be/fr" target="_blank" style="color: #0000EE;">site officiel de l'Office des étrangers</a>.
            </p>
            
            <p style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                <span style="color: #dc3545; border: 1px solid #dc3545; padding: 10px; border-radius: 10px;">
                    Télécharger : 
                    <a
                        href="{visa_application_document_link}"
                        target="_blank"
                        style="color: #dc3545";
                    >Formulaire pour la demande de visa</a>
                </span>
            </p>

            <p>
                Afin de finaliser votre inscription à l'Université, nous vous remercions de nous transmettre 
                l'autorisation signée ainsi que les éventuels documents complémentaires à l'adresse ci-dessous. 
                Nous vous rappelons qu'il est impératif de nous renvoyer ces documents après l'obtention de votre visa.
            </p>

            <p style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                <span style="color: #0000EE; border: 1px solid #0000EE; padding: 10px; border-radius: 10px;">
                    Envoyer à : 
                    <a href="mailto:{admission_email}" target="_blank" style="color: #0000EE;">
                        {admission_email}
                    </a>
                </span>
            </p>

            <p>
                Pour toute question relative à l'inscription, nous vous invitons à consulter 
                <a href="https://uclouvain.be/fr/etudier/inscriptions" target="_blank" style="color: #0000EE;">notre site</a>.
            </p>

            <p>
                Nous vous informons que le début de l'année académique est fixé au {academic_year_start_date} 
                (<a href="https://uclouvain.be/fr/etudier/calendrier-academique.html" target="_blank" style="color: #0000EE;">Calendrier 
                académique</a>).
            </p>

            <p>
                Si vous avez des questions concernant votre arrivée en Belgique, vous avez à votre disposition 
                toute une série d'informations sur 
                <a href="https://uclouvain.be/fr/etudier/inscriptions/bienvenue-aux-etudiants-internationaux-et-aux-etudiantes-internationales.html" target="_blank" style="color: #0000EE;">
                notre page</a>.
            </p>

            <p>
                Nous vous souhaitons la bienvenue à l'UCLouvain.
            </p>
            <br>

            <p>
                Veuillez agréer l'expression de nos salutations distinguées.
            </p>

            <p>
                Le Service des inscriptions
            </p>
            ''',
            },
        ),
    ]
