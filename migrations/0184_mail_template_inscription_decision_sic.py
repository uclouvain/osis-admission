# Generated by Django 3.2.25 on 2024-05-17 14:09

from django.db import migrations
from osis_mail_template import MailTemplateMigration

from admission.mail_templates import INSCRIPTION_EMAIL_SIC_APPROVAL


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0183_update_continuing_status_and_admission_task_type'),
    ]

    operations = [
        MailTemplateMigration(
            INSCRIPTION_EMAIL_SIC_APPROVAL,
            {
                'en': '{academic_year} enrolment application: provisional enrolment',
                'fr-be': "Demande d'inscription {academic_year} :  inscription provisoire",
            },
            {
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
