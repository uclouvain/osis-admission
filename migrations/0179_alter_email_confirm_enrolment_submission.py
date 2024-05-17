from django.db import migrations
from osis_mail_template import MailTemplateMigration

from admission.mail_templates import ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0178_update_working_list_admission_choices'),
    ]

    operations = [
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL,
            {
                'en': 'Your enrolment application ({admission_reference} {candidate_last_name} '
                '{candidate_first_name} {training_acronym})',
                'fr-be': "Suite de votre demande d'inscription ({admission_reference} {candidate_last_name} "
                "{candidate_first_name} {training_acronym})",
            },
            {
                'en': '''
    <p>
       Madam, Sir,
    </p>

    <br/>

    <p>
        The UCLouvain Enrolment Office confirms that it has received your enrolment application, 
        bearing the reference number {admission_reference}.
    </p>

    {payment_sentence}

    {late_enrolment_sentence}

    {enrolment_sentence}

    <p>
        Provided that your application is complete, we will analyse it as soon as possible and keep you informed of its
         status.
    </p>

    <p>
        The Enrolment Office reserves the right to ask you for additional documentation, which must reach us 
        <strong>within 15 calendar days of the request</strong>. If it does not, your application will no longer be 
        considered.
    </p>

    <p>
        Please note that a copy of your file can be downloaded at <a href="{recap_link}">{recap_link}</a>.
    </p>

    <br/>

    <p>
        We thank you for the confidence you have placed in our institution.
    </p>

    <p>
        The UCLouvain Enrolment Office
    </p>

                ''',
                'fr-be': '''
    <p>
        {salutation} {candidate_first_name} {candidate_last_name},
    </p>

    <br/>

    <p>
        Le Service des inscriptions de l'UCLouvain vous confirme avoir reçu une demande d'admission de votre part 
        qui porte le numéro de référence {admission_reference}.
    </p>

    {payment_sentence}

    {late_enrolment_sentence}

    {enrolment_sentence}

    <p>
        Pour autant que votre dossier soit complet, nous analyserons votre demande dans les meilleurs délais et 
        ne manquerons pas de vous faire part de son suivi.
    </p>

    <p>
        Le Service des inscriptions se réserve le droit de vous demander tout justificatif supplémentaire qu'il 
        jugerait utile. Celui-ci devra nous parvenir <strong>impérativement dans les 15 jours calendrier</strong> 
        qui suivent l'envoi de la demande de justificatif. A défaut, votre demande sera clôturée.
    </p>

    <p>
        Sachez qu'une copie de votre dossier est téléchargeable à la page suivante : 
        <a href="{recap_link}" target="_blank">{recap_link}</a>.
    </p>

    <br/>

    <p>
        Nous vous remercions pour la confiance placée dans notre Institution.
    </p>

    <p>
        Le Service des inscriptions de l'UCLouvain.
    </p>
                ''',
            },
        ),
    ]
