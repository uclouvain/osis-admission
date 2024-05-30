from django.db import migrations
from osis_mail_template import MailTemplateMigration

from admission.mail_templates import (
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_CONTINUING,
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_CONTINUING,
)


def remove_continuing_sic_request_mail(apps, schema_editor):
    MailTemplate = apps.get_model('osis_mail_template', 'MailTemplate')
    MailTemplate.objects.filter(identifier='osis-admission-request-sic-documents-continuing').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0181_alter_baseadmission_valuated_secondary_studies_person'),
    ]

    DOCUMENT_SUBMISSION_CONFIRM_TEMPLATE_OBJECT = {
        'en': 'UCLouvain enrolment ({admission_reference}) : acknowledgement of receipt of your documents',
        'fr-be': "Inscription UCLouvain – accusé de réception de vos documents ({admission_reference})",
    }

    DOCUMENT_SUBMISSION_CONFIRM_CONTENT_TEMPLATE_WITH_SUBMITTED_AND_NOT_SUBMITTED = {
        'en': '''<p>{salutation} {candidate_first_name} {candidate_last_name},</p>

                <p>
                    Concerning your application for admission to the {training_title} ({training_campus}) 
                    ({training_acronym}) course for the {training_year} academic year, we confirm receipt of the 
                    following required documents:
                </p>

                {requested_submitted_documents}

                <p>
                    We will evaluate your documents as quickly as possible and get back to you if they are incomplete 
                    or incorrect.
                </p>

                <p>
                    We remind you that the documents listed below have not yet been received. Please send them as soon 
                    as possible to <a href="mailto:{enrolment_service_email}">{enrolment_service_email}</a>:
                </p>

                {requested_not_submitted_documents}

                <p>
                    Sincerely,
                </p>

                <p>
                    The Enrolment Office
                </p>

                        ''',
        'fr-be': '''<p>{salutation} {candidate_first_name} {candidate_last_name},</p>

        <p>
            Dans le cadre de votre demande d'inscription au programme {training_title} ({training_campus}) - 
            {training_acronym} pour l'année académique {training_year}, nous vous confirmons avoir bien reçu les 
            documents suivants indispensables à l’analyse de votre inscription :
        </p>

        {requested_submitted_documents}

        <p>
            Nous procéderons à l’analyse de vos documents dans les meilleurs délais. Nous reviendrons vers vous si vos documents 
            s’avéraient être incomplets ou incorrects.
        </p>

        <p>
            Nous vous rappelons que certains documents n’ont pas été fournis à ce jour, et vous invitons à les fournir 
            dès que possible à l’adresse <a href="mailto:{enrolment_service_email}">{enrolment_service_email}</a> :
        </p>

        {requested_not_submitted_documents}

        <p>
            Veuillez agréer l'expression de nos salutations distinguées.
        </p>

        <p>
            Le Service des inscriptions
        </p>
        ''',
    }
    DOCUMENT_SUBMISSION_CONFIRM_CONTENT_TEMPLATE_WITH_SUBMITTED = {
        'en': '''<p>{salutation} {candidate_first_name} {candidate_last_name},</p>

                <p>
                    Concerning your application for admission to the {training_title} ({training_campus}) 
                    ({training_acronym}) course for the {training_year} academic year, we confirm receipt of the 
                    following required documents:
                </p>

                {requested_submitted_documents}

                <p>
                    We will evaluate your documents as quickly as possible and get back to you if they are incomplete 
                    or incorrect.
                </p>

                <p>
                    Sincerely,
                </p>

                <p>
                    The Enrolment Office
                </p>

                        ''',
        'fr-be': '''<p>{salutation} {candidate_first_name} {candidate_last_name},</p>

        <p>
            Dans le cadre de votre demande d'inscription au programme {training_title} ({training_campus}) - 
            {training_acronym} pour l'année académique {training_year}, nous vous confirmons avoir bien reçu les 
            documents suivants indispensables à l’analyse de votre inscription :
        </p>

        {requested_submitted_documents}

        <p>
            Nous procéderons à l’analyse de vos documents dans les meilleurs délais. Nous reviendrons vers vous si vos documents 
            s’avéraient être incomplets ou incorrects.
        </p>

        <p>
            Veuillez agréer l'expression de nos salutations distinguées.
        </p>

        <p>
            Le Service des inscriptions
        </p>
        ''',
    }

    operations = [
        # Remove the mail template related to the document request by the central manager for the continuing admissions
        migrations.RunPython(
            code=remove_continuing_sic_request_mail,
            reverse_code=migrations.RunPython.noop,
        ),
        # Add the mail templates related to the confirmation of the document submission by the candidate
        MailTemplateMigration(
            ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_CONTINUING,
            DOCUMENT_SUBMISSION_CONFIRM_TEMPLATE_OBJECT,
            DOCUMENT_SUBMISSION_CONFIRM_CONTENT_TEMPLATE_WITH_SUBMITTED_AND_NOT_SUBMITTED,
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_CONTINUING,
            DOCUMENT_SUBMISSION_CONFIRM_TEMPLATE_OBJECT,
            DOCUMENT_SUBMISSION_CONFIRM_CONTENT_TEMPLATE_WITH_SUBMITTED,
        ),
    ]
