# Generated by Django 3.2.12 on 2022-08-22 15:19

from django.db import migrations

from admission.mail_templates import (
    ADMISSION_EMAIL_CANDIDATE_DOCTORAL_TRAINING_NEEDS_UPDATE,
    ADMISSION_EMAIL_CANDIDATE_DOCTORAL_TRAINING_REFUSED,
    ADMISSION_EMAIL_REFERENCE_PROMOTER_DOCTORAL_TRAININGS_SUBMITTED,
)
from osis_mail_template import MailTemplateMigration


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0061_supervisionactor_is_reference_promoter'),
    ]

    operations = [
        MailTemplateMigration(
            ADMISSION_EMAIL_REFERENCE_PROMOTER_DOCTORAL_TRAININGS_SUBMITTED,
            {
                'en': '[OSIS] New doctoral training activities been submitted by {student_first_name} {student_last_name}',
                'fr-be': "[OSIS] De nouvelles activités de formation doctorale ont été soumises par {student_first_name} "
                "{student_last_name}",
            },
            {
                'en': '''<p>Hello,</p>

        <p>
            {student_first_name} {student_last_name} have submitted new doctoral training activities {training_title}, 
            you can review them by following this link: {admission_link_front_doctoral_training}.
        </p>

        <p>
            ---<br/>
            The OSIS Team
        </p>
        ''',
                'fr-be': '''<p>Bonjour,</p>

        <p>
            {student_first_name} {student_last_name} a soumis de nouvelles activités de formation doctorale pour son {training_title},
            vous pouvez les consulter en suivant ce lien : {admission_link_front_doctoral_training}.
        </p>

        <p>
            ---<br/>
            L'équipe OSIS
        </p>
        ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CANDIDATE_DOCTORAL_TRAINING_REFUSED,
            {
                'en': '[OSIS] A doctoral training activity has been refused',
                'fr-be': "[OSIS] Une activité de formation doctorale a été refusée",
            },
            {
                'en': '''<p>Hello,</p>

        <p>
            A submitted doctoral training activity for your {training_title} has been refused, 
            you can review all activities by following this link: {admission_link_front_doctoral_training}.
            
            Here's the reason for this refusal: {reason}
        </p>

        <p>
            ---<br/>
            The OSIS Team
        </p>
        ''',
                'fr-be': '''<p>Bonjour,</p>

        <p>
            Un activité activité de formation doctorale soumis pour votre {training_title} a été refusée,
            vous pouvez les consulter en suivant ce lien : {admission_link_front_doctoral_training}.
            
            La raison invoquée pour ce refus : {reason}
        </p>

        <p>
            ---<br/>
            L'équipe OSIS
        </p>
        ''',
            },
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_CANDIDATE_DOCTORAL_TRAINING_NEEDS_UPDATE,
            {
                'en': '[OSIS] A doctoral training activity needs to be updated',
                'fr-be': "[OSIS] Une activité de formation doctorale doit être mise à jour",
            },
            {
                'en': '''<p>Hello,</p>

        <p>
            A submitted doctoral training activity for {training_title} must be updated, 
            you can review them by following this link: {admission_link_front_doctoral_training}.
            
            Here's  why it need to be updated: {reason}
        </p>

        <p>
            ---<br/>
            The OSIS Team
        </p>
        ''',
                'fr-be': '''<p>Bonjour,</p>

        <p>
            Une activité de formation doctorale doit être mise à jour pour {training_title},
            vous pouvez les consulter en suivant ce lien : {admission_link_front_doctoral_training}.

            Voici ce pourquoi vous devez la modifier : {reason}
        </p>

        <p>
            ---<br/>
            L'équipe OSIS
        </p>
        ''',
            },
        ),
    ]
