# Generated by Django 3.2.25 on 2024-07-08 15:17

from django.db import migrations
from osis_mail_template import MailTemplateMigration

from admission.mail_templates import (
    ADMISSION_EMAIL_SIC_APPROVAL_DOCTORATE,
    ADMISSION_EMAIL_SIC_APPROVAL_EU_DOCTORATE,
    INSCRIPTION_EMAIL_SIC_APPROVAL_DOCTORATE,
)


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0229_merge_20241028_1046'),
    ]

    operations = [
        MailTemplateMigration(
            identifier=ADMISSION_EMAIL_SIC_APPROVAL_DOCTORATE,
            subjects={
                'en': 'Enrolment authorisation ({admission_reference})',
                'fr-be': "Autorisation d'inscription suite à une demande d'admission ({admission_reference})",
            },
            contents={
                'en': '''<p>{greetings} {candidate_first_name} {candidate_last_name},</p>
                <br>

                <p>
                    We are pleased to inform you that you are authorised to enrol in the {training_title} 
                    ({training_campus}) - {training_acronym} for the {academic_year} academic year.
                </p>

                <p>
                    Please download your enrolment authorisation which contains all the relevant information and any 
                    conditions that need to be met before registering, as well as the annex from your PhD Subject 
                    Committee, which contains important information about your doctoral training.
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

                <p style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                    <span style="color: #dc3545; border: 1px solid #dc3545; padding: 10px; border-radius: 10px;">
                        Download: 
                        <a
                            href="{cdd_annex_document_link}"
                            target="_blank"
                            style="color: #dc3545;"
                        >PhD Subject Committee annex</a>
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
                    les éventuelles conditions à remplir préalablement à votre inscription, ainsi que l’annexe de votre 
                    Commission doctorale de domaine qui contient des informations importantes relatives à votre 
                    parcours doctoral.
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

                <p style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                    <span style="color: #dc3545; border: 1px solid #dc3545; padding: 10px; border-radius: 10px;">
                        Télécharger : 
                        <a
                            href="{cdd_annex_document_link}"
                            target="_blank"
                            style="color: #dc3545;"
                        >Annexe CDD</a>
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
        MailTemplateMigration(
            identifier=ADMISSION_EMAIL_SIC_APPROVAL_EU_DOCTORATE,
            subjects={
                'en': 'Enrolment authorisation ({admission_reference})',
                'fr-be': "Autorisation d'inscription suite à une demande d'admission ({admission_reference})",
            },
            contents={
                'en': '''<p>{greetings} {candidate_first_name} {candidate_last_name},</p>
                <br>

                <p>
                    We are pleased to inform you that you are authorised to enrol in the {training_title} 
                    ({training_campus}) - {training_acronym} for the {academic_year} academic year.
                </p>

                <p>
                    Please download your enrolment authorisation which contains all the relevant information and any 
                    conditions that need to be met before registering, as well as the annex from your PhD Subject 
                    Committee, which contains important information about your doctoral training.
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

                <p style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                    <span style="color: #dc3545; border: 1px solid #dc3545; padding: 10px; border-radius: 10px;">
                        Download: 
                        <a
                            href="{cdd_annex_document_link}"
                            target="_blank"
                            style="color: #dc3545;"
                        >PhD Subject Committee annex</a>
                    </span>
                </p>

                <p>
                    Please send us the signed enrolment authorisation and any 
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
                    les éventuelles conditions à remplir préalablement à votre inscription, ainsi que l’annexe de votre 
                    Commission doctorale de domaine qui contient des informations importantes relatives à votre 
                    parcours doctoral.
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

                <p style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                    <span style="color: #dc3545; border: 1px solid #dc3545; padding: 10px; border-radius: 10px;">
                        Télécharger : 
                        <a
                            href="{cdd_annex_document_link}"
                            target="_blank"
                            style="color: #dc3545;"
                        >Annexe CDD</a>
                    </span>
                </p>

                <p>
                    Afin de finaliser votre inscription à l'Université, nous vous remercions de nous transmettre 
                    l'autorisation signée ainsi que les éventuels documents complémentaires à l'adresse ci-dessous.
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
        MailTemplateMigration(
            identifier=INSCRIPTION_EMAIL_SIC_APPROVAL_DOCTORATE,
            subjects={
                'en': '{academic_year} enrolment application: provisional enrolment',
                'fr-be': "Demande d'inscription {academic_year} :  inscription provisoire",
            },
            contents={
                'en': '''<p>Your file number: {admission_reference}</p>
                <p>Dear Prénom Nom,</p> 
                <p>We have the pleasure of informing you that your application for enrolment for the {academic_year} academic year in the programme {training_title} [{training_acronym}] ({training_campus}) has been accepted.</p>

                {contact_person_paragraph}
                {planned_years_paragraph}
                {prerequisite_courses_paragraph}
                {prerequisite_courses_detail_paragraph}

                <p>Your file’s student number (noma) is: {noma} (to be provided when contacting university services).</p>
                <p>You will receive an email as soon as your invoice and enrolment certificates become available in your <a href="https://intranet.uclouvain.be/">"My UCL"</a> virtual office.</p>
                <p>What steps should you take to prepare for the start of the academic year? Find out at <a href="https://uclouvain.be/first-steps">https://uclouvain.be/first-steps</a>.</p>
                <p>Please download the annex from your PhD Subject Committee, which contains important information about your doctoral training.</p>
                <p style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                    <span style="color: #dc3545; border: 1px solid #dc3545; padding: 10px; border-radius: 10px;">
                        Download: 
                        <a
                            href="{cdd_annex_document_link}"
                            target="_blank"
                            style="color: #dc3545;"
                        >PhD Subject Committee annex</a>
                    </span>
                </p>
                <p>We remind you that you have agreed to abide by the UCLouvain regulations, which establish your rights and obligations as a member of the university: <a href="https://uclouvain.be/fr/decouvrir/rgee.html">https://uclouvain.be/fr/decouvrir/rgee.html</a>.</p>

                {required_documents_paragraph}

                <p>We wish you a successful {academic_year} academic year.</p>
                <p>The UCLouvain Enrolment Office</p>
                ''',
                'fr-be': '''<p>Votre numéro de dossier : {admission_reference}</p>
                <p>{greetings} {candidate_first_name} {candidate_last_name}, </p>
                <p>Par la présente, nous avons le plaisir de vous faire savoir que votre demande d'inscription pour
                l’année académique {academic_year} au programme {training_title} [{training_acronym}] ({training_campus})
                a été acceptée.</p>

                {contact_person_paragraph}
                {planned_years_paragraph}
                {prerequisite_courses_paragraph}
                {prerequisite_courses_detail_paragraph}

                <p>Votre dossier porte le numéro de matricule étudiant (noma) suivant : {noma}
                (à rappeler lors de tout contact avec les différents services de l'université).</p>
                <p>Vous recevrez un mail dès que votre facture et vos attestations d’inscription seront disponibles sur votre
                bureau virtuel <a href="https://intranet.uclouvain.be/">(My UCL)</a>.</p>
                <p>Quelles sont les étapes à suivre pour bien préparer votre rentrée ? Toutes les informations utiles sont
                disponibles sur la page <a href="https://uclouvain.be/premiers-pas">https://uclouvain.be/premiers-pas</a>.</p>
                <p>Veuillez télécharger l’annexe de votre Commission doctorale de domaine qui contient des informations 
                importantes relatives à votre parcours doctoral.</p>
                <p style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                    <span style="color: #dc3545; border: 1px solid #dc3545; padding: 10px; border-radius: 10px;">
                        Télécharger : 
                        <a
                            href="{cdd_annex_document_link}"
                            target="_blank"
                            style="color: #dc3545;"
                        >Annexe CDD</a>
                    </span>
                </p>
                <p>Nous vous rappelons que vous avez accepté de respecter les règlements en vigueur à l'UCLouvain qui précisent
                vos droits et obligations en tant que membre de l'université :
                <a href="https://uclouvain.be/fr/decouvrir/rgee.html">https://uclouvain.be/fr/decouvrir/rgee.html</a>.</p>

                {required_documents_paragraph}

                <p>Nous vous souhaitons une fructueuse année académique {academic_year}.</p>
                <p>L'équipe du Service des inscriptions de l’UCLouvain</p>
                ''',
            },
        ),
    ]