from django.db import migrations
from osis_mail_template import MailTemplateMigration

from admission.mail_templates import (
    ADMISSION_EMAIL_CDD_APPROVAL_DOCTORATE_WITH_BELGIAN_DIPLOMA,
    ADMISSION_EMAIL_CDD_APPROVAL_DOCTORATE_WITHOUT_BELGIAN_DIPLOMA,
)


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0278_alter_doctorateadmission_cotutelle_motivation'),
    ]

    operations = [
        MailTemplateMigration(
            identifier=ADMISSION_EMAIL_CDD_APPROVAL_DOCTORATE_WITH_BELGIAN_DIPLOMA,
            subjects={
                'en': "UCLouvain - admission application {admission_reference} follow-up",
                'fr-be': "UCLouvain - suivi de votre demande d'admission - {admission_reference}",
            },
            contents={
                'en': '''<p>{greetings} {candidate_first_name} {candidate_last_name},</p>

                <p>Thank you for your admission application to the {training_acronym} / {training_title} programme
                  for the {academic_year} academic year.</p>

                <p>The PhD Field Committee has approved your application, which is now with the Enrolment Office (SIC).</p>

                <p>A series of practical considerations concerning your PhD are summarised in a document in your document section.</p>

                <p>Please remember that you must enrol for the PhD every year until the academic year in which you defend your thesis.</p>

                {prerequisite_courses_list}
                {prerequisite_courses_communication}

                <p>{sender_name} - {doctoral_commission}</p>
                ''',
                'fr-be': '''<p>{greetings} {candidate_first_name} {candidate_last_name},</p>

                <p>Votre demande d'admission à l'année académique {academic_year} au programme {training_acronym} / {training_title}
                  nous est bien parvenue et nous vous en remercions.</p>

                <p>Nous vous informons que la Commission doctorale de domaine s’est réunie et qu’elle a validé votre demande;
                  il est actuellement entre les mains du Service des inscriptions (SIC).

                <p>Une série de considérations pratiques liées à votre doctorat sont résumées dans un document se trouvant dans votre espace document.</p>

                <p>Nous vous rappelons que l’inscription au doctorat est annuelle et ce jusqu’à l’année académique de la soutenance.</p>

                {prerequisite_courses_list}
                {prerequisite_courses_communication}

                <p>{sender_name} - {doctoral_commission}</p>
                ''',
            },
        ),
        MailTemplateMigration(
            identifier=ADMISSION_EMAIL_CDD_APPROVAL_DOCTORATE_WITHOUT_BELGIAN_DIPLOMA,
            subjects={
                'en': "UCLouvain - admission application {admission_reference} follow-up",
                'fr-be': "UCLouvain - suivi de votre demande d'admission - {admission_reference}",
            },
            contents={
                'en': '''<p>{greetings} {candidate_first_name} {candidate_last_name},</p>

                <p>Thank you for your admission application to the {training_acronym} / {training_title} programme
                  for the {academic_year} academic year.</p>

                <p>The PhD Field Committee has approved your application, which is now with the Enrolment Office (SIC).</p>

                <p>If it accepts your application, SIC will immediately send you an enrolment authorisation.</p>

                <p>A series of practical considerations concerning your PhD are summarised in a document in your document section.</p>

                <p>Please remember that you must enrol for the PhD every year until the academic year in which you defend your thesis.</p>

                {prerequisite_courses_list}
                {prerequisite_courses_communication}

                <p>{sender_name} - {doctoral_commission}</p>
                ''',
                'fr-be': '''<p>{greetings} {candidate_first_name} {candidate_last_name},</p>

                <p>Votre demande d'admission à l'année académique {academic_year} au programme {training_acronym} / {training_title}
                  nous est bien parvenue et nous vous en remercions.</p>

                <p>Nous vous informons que la Commission doctorale de domaine s’est réunie et qu’elle a validé votre demande;
                  il est actuellement entre les mains du Service des inscriptions (SIC).

                <p>Sous réserve de l’acceptation de votre dossier par le SIC, l’autorisation d’inscription vous sera délivrée par ce service très prochainement.</p>

                <p>Une série de considérations pratiques liées à votre doctorat sont résumées dans un document se trouvant dans votre espace document.</p>

                <p>Nous vous rappelons que l’inscription au doctorat est annuelle et ce jusqu’à l’année académique de la soutenance.</p>

                {prerequisite_courses_list}
                {prerequisite_courses_communication}

                <p>{sender_name} - {doctoral_commission}</p>
                ''',
            },
        ),
    ]
