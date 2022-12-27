from django.db import migrations

from admission.mail_templates import (
    ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI,
)
from osis_mail_template import MailTemplateMigration


def remove_templates(apps, _):
    templates_to_delete = [
        'osis-admission-confirmation-extension-request-cdd-opinion-student',
        'osis-admission-confirmation-submission-by-promoter-adre',
        ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
        ADMISSION_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE,
        ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT,
        ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE,
        ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI,
        ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
        ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE,
        ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI,
        ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
        ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE,
        ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI,
    ]
    MailTemplate = apps.get_model('osis_mail_template', 'MailTemplate')
    MailTemplate.objects.filter(identifier__in=templates_to_delete).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0052_confirmation_paper_order_by_id'),
        ('osis_mail_template', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(remove_templates, migrations.RunPython.noop),
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE,
            {
                'en': '[OSIS] The confirmation form has been submitted by {student_first_name} {student_last_name} '
                '(Financing: {scholarship_grant_acronym})',
                'fr-be': "[OSIS] Le formulaire d'épreuve de confirmation a été soumis par {student_first_name} "
                "{student_last_name} (Financement : {scholarship_grant_acronym})",
            },
            {
                'en': '''<p>Hello,</p>

    <p>
        {student_first_name} {student_last_name} has submitted the confirmation form for the {training_title} 
        (Financing: {scholarship_grant_acronym}).
    </p>

    <p>
        ---<br/>
        The OSIS Team
    </p>
    ''',
                'fr-be': '''<p>Bonjour,</p>

    <p>
        {student_first_name} {student_last_name} a soumis son formulaire de confirmation pour son {training_title} 
        (Financement : {scholarship_grant_acronym}).
    </p>

    <p>
        ---<br/>
        L'équipe OSIS
    </p>
    ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
            {
                'en': '[OSIS] Information for the organisation of your confirmation paper scheduled on '
                '{confirmation_paper_date}',
                'fr-be': '[OSIS] Informations pour l’organisation de votre épreuve de confirmation prévue le '
                '{confirmation_paper_date}',
            },
            {
                'en': '''<p>Hello {student_first_name} {student_last_name},</p>

            <p>
                In order to best prepare your confirmation paper, we would like to inform you that you are responsible
                for:
            </p>

            <ul>
                <li>Organizing the event,</li>
                <li>Ensuring the availability of the supervisory panel,</li>
                <li>Book the room,</li>
                <li>Sending your research report to the members of the supervisory panel,</li>
                <li>
                    Uploading your research report to OSIS by clicking 
                    <a href="{confirmation_paper_link_front}">here</a>.
                </li>
            </ul>

            <p>
                We also remind you that 20 credits must be obtained before the confirmation paper.
            </p>

            <p>
                Regards,
            </p>

            <p>
                ---<br/>
                The OSIS Team
            </p>
                ''',
                'fr-be': '''<p>Bonjour,</p>

            <p>
                Afin de préparer au mieux votre épreuve de confirmation, nous vous précisons que vous êtes chargé :
            </p>

            <ul>
                <li>De l’organisation de l’épreuve,</li>
                <li>De vous assurer de la disponibilité du comité d’accompagnement,</li>
                <li>De réserver la salle,</li>
                <li>D’envoyer votre rapport de recherche aux membre du comité d’accompagnement,</li>
                <li>
                    De téléverser votre rapport de recherche dans OSIS en cliquant 
                    <a href="{confirmation_paper_link_front}">ici</a>.
                </li>
            </ul>
            
            <p>
                Nous vous rappelons également que le nombre de crédits à obtenir avant l’épreuve de confirmation est de 
                20 ECTS.
            </p>
            
            <p>
                Bien cordialement,
            </p>

            <p>
                ---<br/>
                L'équipe OSIS
            </p>
                ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT,
            {
                'en': '[OSIS] Success of your confirmation paper',
                'fr-be': '[OSIS] Réussite de votre épreuve de confirmation',
            },
            {
                'en': '''<p>Hello {student_first_name} {student_last_name},</p>

    <p>
        We would like to inform you that you have passed your confirmation paper taken on {confirmation_paper_date} 
        for your {training_title}.
    </p>

    <p>
        Your certificate of achievement is available <a href="{confirmation_paper_link_front}">here</a>.
    </p>

    <p>
        ---<br/>
        The OSIS Team
    </p>
        ''',
                'fr-be': '''<p>Bonjour {student_first_name} {student_last_name},</p>

    <p>
        Nous tenons à vous informer que vous avez réussi votre épreuve de confirmation passée le 
        {confirmation_paper_date} pour votre {training_title}.
    </p>

    <p>
        Votre certificat de réussite est disponible <a href="{confirmation_paper_link_front}">ici</a>.
    </p>

    <p>
        ---<br/>
        L'équipe OSIS
    </p>
        ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE,
            {
                'en': '[OSIS] Success of the confirmation paper of {student_first_name} {student_last_name} '
                '(Financing: {scholarship_grant_acronym}) - {training_title}',
                'fr-be': "[OSIS] Réussite de l'épreuve de confirmation de {student_first_name} "
                "{student_last_name} (Financement : {scholarship_grant_acronym}) - {training_title}",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    {student_first_name} {student_last_name} has passed the confirmation paper on {confirmation_paper_date} 
    for the {training_title} (Financing: {scholarship_grant_acronym}).
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    {student_first_name} {student_last_name} a réussi son épreuve de confirmation le {confirmation_paper_date} 
    pour son {training_title} (Financement : {scholarship_grant_acronym}).
</p>

<p>
    ---<br/>
    L'équipe OSIS
</p>
    ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI,
            {
                'en': '[OSIS] Success of the confirmation paper of {student_first_name} {student_last_name} '
                '(Financing: {scholarship_grant_acronym}) - {training_title}',
                'fr-be': "[OSIS] Réussite de l'épreuve de confirmation de {student_first_name} "
                "{student_last_name} (Financement : {scholarship_grant_acronym}) - {training_title}",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    {student_first_name} {student_last_name} has passed the confirmation paper on {confirmation_paper_date} 
    for the {training_title} (Financing: {scholarship_grant_acronym}).
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    {student_first_name} {student_last_name} a réussi son épreuve de confirmation le {confirmation_paper_date} 
    pour son {training_title} (Financement : {scholarship_grant_acronym}).
</p>

<p>
    ---<br/>
    L'équipe OSIS
</p>
                ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
            {
                'en': '[OSIS] Failure of your confirmation paper',
                'fr-be': '[OSIS] Échec à votre épreuve de confirmation',
            },
            {
                'en': '''<p>Hello {student_first_name} {student_last_name},</p>

<p>
    We would like to inform you that you have failed your confirmation paper taken on {confirmation_paper_date} 
    for your {training_title}.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour {student_first_name} {student_last_name},</p>

<p>
    Nous tenons à vous informer que vous avez échoué à votre épreuve de confirmation passée le 
    {confirmation_paper_date} pour votre {training_title}.
</p>

<p>
    ---<br/>
    L'équipe OSIS
</p>
    ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE,
            {
                'en': '[OSIS] Failure of the confirmation paper of {student_first_name} {student_last_name} '
                '(Financing: {scholarship_grant_acronym}) - {training_title}',
                'fr-be': "[OSIS] Échec de l'épreuve de confirmation de {student_first_name} "
                "{student_last_name} (Financement : {scholarship_grant_acronym}) - {training_title}",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    {student_first_name} {student_last_name} has failed the confirmation paper on {confirmation_paper_date} 
    for the {training_title} (Financing: {scholarship_grant_acronym}).
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    {student_first_name} {student_last_name} a échoué à son épreuve de confirmation le {confirmation_paper_date} 
    pour son {training_title} (Financement : {scholarship_grant_acronym}).
</p>

<p>
    ---<br/>
    L'équipe OSIS
</p>
    ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI,
            {
                'en': '[OSIS] Failure of the confirmation paper of {student_first_name} {student_last_name} '
                '(Financing: {scholarship_grant_acronym}) - {training_title}',
                'fr-be': "[OSIS] Échec de l'épreuve de confirmation de {student_first_name} "
                "{student_last_name} (Financement : {scholarship_grant_acronym}) - {training_title}",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    {student_first_name} {student_last_name} has failed the confirmation paper on {confirmation_paper_date} 
    for the {training_title} (Financing: {scholarship_grant_acronym}).
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    {student_first_name} {student_last_name} a échoué à son épreuve de confirmation le {confirmation_paper_date} 
    pour son {training_title} (Financement : {scholarship_grant_acronym}).
</p>

<p>
    ---<br/>
    L'équipe OSIS
</p>
                ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
            {
                'en': '[OSIS] Need to retake your confirmation test',
                'fr-be': '[OSIS] Nécessité de repasser votre épreuve de confirmation',
            },
            {
                'en': '''<p>Hello {student_first_name} {student_last_name},</p>

<p>
    As a result of your confirmation paper, taken on {confirmation_paper_date} for your {training_title}, 
    the supervisory panel has decided that it is necessary for you to retake it.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour {student_first_name} {student_last_name},</p>

<p>
    Nous tenons à vous informer que suite à votre épreuve de confirmation du {confirmation_paper_date} pour votre 
    {training_title}, le comité d’accompagnement a acté qu’il est nécessaire que vous repassiez à nouveau votre 
    épreuve de confirmation.
</p>

<p>
    ---<br/>
    L'équipe OSIS
</p>
    ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE,
            {
                'en': "[OSIS] {student_first_name} {student_last_name} must retake the confirmation paper "
                "(Financing: {scholarship_grant_acronym}) - {training_title})",
                'fr-be': "[OSIS] {student_first_name} {student_last_name} doit repasser son épreuve de confirmation "
                "(Financement : {scholarship_grant_acronym}) - {training_title})",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    As a result of the confirmation paper of {student_first_name} {student_last_name}, taken on 
    {confirmation_paper_date} for the {training_title} (Funding: {scholarship_grant_acronym}), the supervisory panel 
    has decided that it is necessary for the doctoral student to retake it.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    Suite à l’épreuve de confirmation de {student_first_name} {student_last_name}, réalisée le 
    {confirmation_paper_date} pour son {training_title} (Financement : {scholarship_grant_acronym}), le comité 
    d’accompagnement a acté qu’il était nécessaire que le doctorand repasse son épreuve de confirmation.
</p>

<p>
    ---<br/>
    L'équipe OSIS
</p>
    ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI,
            {
                'en': "[OSIS] {student_first_name} {student_last_name} must retake the confirmation paper "
                "(Financing: {scholarship_grant_acronym}) - {training_title})",
                'fr-be': "[OSIS] {student_first_name} {student_last_name} doit repasser son épreuve de confirmation "
                "(Financement : {scholarship_grant_acronym}) - {training_title})",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    As a result of the confirmation paper of {student_first_name} {student_last_name}, taken on 
    {confirmation_paper_date} for the {training_title} (Funding: {scholarship_grant_acronym}), the supervisory panel 
    has decided that it is necessary for the doctoral student to retake it.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    Suite à l’épreuve de confirmation de {student_first_name} {student_last_name}, réalisée le 
    {confirmation_paper_date} pour son {training_title} (Financement : {scholarship_grant_acronym}), le comité 
    d’accompagnement a acté qu’il était nécessaire que le doctorand repasse son épreuve de confirmation.
</p>

<p>
    ---<br/>
    L'équipe OSIS
</p>
    ''',
            },
        ),
    ]
