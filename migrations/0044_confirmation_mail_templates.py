from django.db import migrations

from admission.mail_templates import (
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
)
from osis_mail_template import MailTemplateMigration


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0043_generic_mail_template'),
        ('osis_mail_template', '0001_initial'),
    ]

    operations = [
        MailTemplateMigration(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE,
            {
                'en': '[OSIS] A phd student has submitted his confirmation form ({scholarship_grant_acronym})',
                'fr-be': "[OSIS] Un doctorant a soumis son formulaire de confirmation ({scholarship_grant_acronym})",
            },
            {
                'en': '''<p>Hello,</p>

<p>
    {student_first_name} {student_last_name} has submitted his confirmation form for its {training_title}.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
''',
                'fr-be': '''<p>Bonjour,</p>

<p>
    {student_first_name} {student_last_name} a soumis son formulaire de confirmation pour son {training_title}.
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
                'en': '[OSIS] Result of your confirmation paper',
                'fr-be': '[OSIS] Résultat de votre épreuve de confirmation',
            },
            {
                'en': '''<p>Hello {student_first_name} {student_last_name},</p>

<p>
    You have recently taken the confirmation paper (on {confirmation_paper_date}) for your {training_title}.
</p>

<p>
    We would like to inform you that you have passed it.
</p>

<p>
    You can retrieve the certificate of achievement <a href="{confirmation_paper_link_front}">here</a>.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour {student_first_name} {student_last_name},</p>

<p>
    Vous avez récemment passé l'épreuve de confirmation (le {confirmation_paper_date}) pour votre {training_title}.
</p>

<p>
    Nous tenons à vous informer que vous avez réussi cette épreuve.
</p>

<p>
    Vous pouvez récupérer le certificat de réussite <a href="{confirmation_paper_link_front}">ici</a>.
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
    You have recently taken the confirmation paper (on {confirmation_paper_date}) for your {training_title}.
</p>

<p>
    Unfortunately, you did not pass this paper.
</p>

<p>
    ---<br/>
    The OSIS Team
</p>
    ''',
                'fr-be': '''<p>Bonjour {student_first_name} {student_last_name},</p>

<p>
    Vous avez récemment passé l'épreuve de confirmation (le {confirmation_paper_date}) pour votre {training_title}.
</p>

<p>
    Malheureusement, vous n'avez pas réussi cette épreuve.
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
    You have recently taken the confirmation paper (on {confirmation_paper_date}) for your {training_title}.
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
    Vous avez récemment passé l'épreuve de confirmation (le {confirmation_paper_date}) pour votre {training_title}.
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
    for its {training_title}.
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
    pour son {training_title}.
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
    for its {training_title}.
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
    pour son {training_title}.
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
    for its {training_title}.
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
    pour son {training_title}.
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
    for its {training_title}.
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
    pour son {training_title}.
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
    for its {training_title}.
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
    pour son {training_title}.
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
    for its {training_title}.
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
    pour son {training_title}.</p>
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
