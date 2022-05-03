from django.db import migrations

from admission.mail_templates import (
    ADMISSION_EMAIL_CONFIRMATION_PAPER_EXTENSION_REQUEST_CDD_OPINION_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_SUBMISSION_BY_PROMOTER_ADRE,
)
from osis_mail_template import MailTemplateMigration


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0043_generic_mail_template'),
        ('osis_mail_template', '0001_initial'),
    ]

    operations = [
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_SUBMISSION_BY_PROMOTER_ADRE,
            {
                'en': '[OSIS] A promoter uploaded documents related to one of its '
                      'supervised confirmation paper ({scholarship_grant_acronym})',
                'fr-be': "[OSIS] Un promoteur a téléversé des documents relatifs à "
                         "une des épreuves de confirmation qu'il supervise ({scholarship_grant_acronym})",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    {promoter_first_name} {promoter_last_name} uploaded documents related to the confirmation paper of the 
    {student_first_name} {student_last_name} for its {doctorate_title}.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    {promoter_first_name} {promoter_last_name} a téléversé des documents relatifs à l'épreuve de confirmation de 
    {student_first_name} {student_last_name} pour son {doctorate_title}.
</p>

<p>
    ---<br/>
    L'équipe OSIS
</p>
''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE,
            {
                'en': '[OSIS] A phd student has submitted his confirmation form ({scholarship_grant_acronym})',
                'fr-be': "[OSIS] Un doctorant a soumis son formulaire de confirmation ({scholarship_grant_acronym})",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    {student_first_name} {student_last_name} has submitted his confirmation form for its {doctorate_title}.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    {student_first_name} {student_last_name} a soumis son formulaire de confirmation pour son {doctorate_title}.
</p>

<p>
    ---<br/>
    L'équipe OSIS
</p>
''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_EXTENSION_REQUEST_CDD_OPINION_STUDENT,
            {
                'en': '[OSIS] Response to the extension request related to your confirmation paper',
                'fr-be': '[OSIS] Réponse à la demande de prolongation relative à votre épreuve de confirmation',
            },
            {
                'en': '''<p>Hello {student_first_name} {student_last_name},</p>

<p>
    You have recently requested a new deadline ({extension_request_proposed_date}) for the confirmation paper of 
    your {doctorate_title}.
</p>

<p>
    Your DDC manager gave his opinion about it:
</p>

<blockquote>
    <p>{extension_request_cdd_opinion}</p>
</blockquote>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour {student_first_name} {student_last_name},</p>

<p>
    Vous avez récemment proposé une nouvelle échéance ({extension_request_proposed_date}) pour l'épreuve de 
    confirmation de votre {doctorate_title}.
</p>

<p>
    Votre gestionnaire CDD a donné son avis à ce sujet :
</p>
<blockquote>
    <p>{extension_request_cdd_opinion}</p>
</blockquote>

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
                'en': '[OSIS] Result of your confirmation paper',
                'fr-be': '[OSIS] Résultat de votre épreuve de confirmation',
            },
            {
                'en': '''<p>Hello {student_first_name} {student_last_name},</p>

<p>
    You have recently taken the confirmation paper (on {confirmation_paper_date}) for your {doctorate_title}.
</p>

<p>
    We would like to inform you that you have passed it.
</p>

<p>
    You can retrieve the certificate of achievement <a href="{certificate_of_achievement_link}">here</a>.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour {student_first_name} {student_last_name},</p>

<p>
    Vous avez récemment passé l'épreuve de confirmation (le {confirmation_paper_date}) pour votre {doctorate_title}.
</p>

<p>
    Nous tenons à vous informer que vous avez réussi cette épreuve.
</p>

<p>
    Vous pouvez récupérer le certificat de réussite <a href="{certificate_of_achievement_link}">ici</a>.
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
                'en': '[OSIS] Result of your confirmation paper',
                'fr-be': '[OSIS] Résultat de votre épreuve de confirmation',
            },
            {
                'en': '''<p>Hello {student_first_name} {student_last_name},</p>

<p>
    You have recently taken the confirmation paper (on {confirmation_paper_date}) for your {doctorate_title}.
</p>

<p>
    Unfortunately, you did not pass this paper.
</p>

<p>
    You can retrieve the certificate of failure <a href="{certificate_of_failure_link}">here</a>.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour {student_first_name} {student_last_name},</p>

<p>
    Vous avez récemment passé l'épreuve de confirmation (le {confirmation_paper_date}) pour votre {doctorate_title}.
</p>

<p>
    Malheureusement, vous n'avez pas réussi cette épreuve.
</p>

<p>
    Vous pouvez récupérer le certificat d'échec <a href="{certificate_of_failure_link}">ici</a>.
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
                'en': '[OSIS] Result of your confirmation paper',
                'fr-be': '[OSIS] Résultat de votre épreuve de confirmation',
            },
            {
                'en': '''<p>Hello {student_first_name} {student_last_name},</p>

<p>
    You have recently taken the confirmation paper (on {confirmation_paper_date}) for your {doctorate_title}.
</p>

<p>
    Unfortunately, you did not pass it. But you will be able to retake it later.
<p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour {student_first_name} {student_last_name},</p>

<p>
    Vous avez récemment passé l'épreuve de confirmation (le {confirmation_paper_date}) pour votre {doctorate_title}.
</p>

<p>
    Malheureusement, vous n'avez pas réussi cette épreuve. Cependant, vous pourrez la repasser plus tard.
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
                'en': '[OSIS] Result of a confirmation paper ({scholarship_grant_acronym})',
                'fr-be': "[OSIS] Résultat d'une épreuve de confirmation ({scholarship_grant_acronym})",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    {student_first_name} {student_last_name} has recently taken the confirmation paper (on {confirmation_paper_date}) 
    for its {doctorate_title}.
</p>

<p>
    We would like to inform you that he has passed it.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    {student_first_name} {student_last_name} a récemment passé l'épreuve de confirmation (le {confirmation_paper_date}) 
    pour son {doctorate_title}.
</p>

<p>
    Nous tenons à vous informer qu'il a réussi cette épreuve.
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
                'en': '[OSIS] Result of a confirmation paper ({scholarship_grant_acronym})',
                'fr-be': "[OSIS] Résultat d'une épreuve de confirmation ({scholarship_grant_acronym})",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    {student_first_name} {student_last_name} has recently taken the confirmation paper (on {confirmation_paper_date}) 
    for its {doctorate_title}.
</p>

<p>
    We would like to inform you that he has passed it.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    {student_first_name} {student_last_name} a récemment passé l'épreuve de confirmation (le {confirmation_paper_date}) 
    pour son {doctorate_title}.
</p>

<p>
    Nous tenons à vous informer qu'il a réussi cet épreuve.
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
                'en': '[OSIS] Result of a confirmation paper ({scholarship_grant_acronym})',
                'fr-be': "[OSIS] Résultat d'une épreuve de confirmation ({scholarship_grant_acronym})",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    {student_first_name} {student_last_name} has recently taken the confirmation paper (on {confirmation_paper_date}) 
    for its {doctorate_title}.
</p>

<p>
    We would like to inform you that he hasn't passed it.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    {student_first_name} {student_last_name} a récemment passé l'épreuve de confirmation (le {confirmation_paper_date}) 
    pour son {doctorate_title}.
</p>

<p>
    Nous tenons à vous informer qu'il n'a pas réussi cette épreuve.
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
                'en': '[OSIS] Result of a confirmation paper ({scholarship_grant_acronym})',
                'fr-be': "[OSIS] Résultat d'une épreuve de confirmation ({scholarship_grant_acronym})",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    {student_first_name} {student_last_name} has recently taken the confirmation paper (on {confirmation_paper_date}) 
    for its {doctorate_title}.
</p>

<p>
    We would like to inform you that he hasn't passed it.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    {student_first_name} {student_last_name} a récemment passé l'épreuve de confirmation (le {confirmation_paper_date}) 
    pour son {doctorate_title}.
</p>

<p>
    Nous tenons à vous informer qu'il n'a pas réussi cette épreuve.
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
                'en': '[OSIS] Result of a confirmation paper ({scholarship_grant_acronym})',
                'fr-be': "[OSIS] Résultat d'une épreuve de confirmation ({scholarship_grant_acronym})",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    {student_first_name} {student_last_name} has recently taken the confirmation paper (on {confirmation_paper_date}) 
    for its {doctorate_title}.
</p>

<p>
    We would like to inform you that he hasn't passed it but will be able to retake it later.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    {student_first_name} {student_last_name} a récemment passé l'épreuve de confirmation (le {confirmation_paper_date}) 
    pour son {doctorate_title}.
</p>

<p>
    Nous tenons à vous informer qu'il n'a pas réussi cette épreuve mais qu'il pourra la repasser plus tard.
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
                'en': '[OSIS] Result of a confirmation paper ({scholarship_grant_acronym})',
                'fr-be': "[OSIS] Résultat d'une épreuve de confirmation ({scholarship_grant_acronym})",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    {student_first_name} {student_last_name} has recently taken the confirmation paper (on {confirmation_paper_date}) 
    for its {doctorate_title}.
</p>

<p>
    We would like to inform you that he hasn't passed it but will be able to retake it later.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    {student_first_name} {student_last_name} a récemment passé l'épreuve de confirmation (le {confirmation_paper_date}) 
    pour son {doctorate_title}.</p>
<p>
    Nous tenons à vous informer qu'il n'a pas réussi cette épreuve mais qu'il pourra la repasser plus tard.
</p>

<p>
    ---<br/>
    L'équipe OSIS
</p>
    ''',
            },
        ),
    ]
