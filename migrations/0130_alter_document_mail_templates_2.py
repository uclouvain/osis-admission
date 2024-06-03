# Generated by Django 3.2.12 on 2022-08-22 15:19

from django.db import migrations

from admission.mail_templates import (
    ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_GENERAL,
    ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_GENERAL,
    ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_DOCTORATE,
    ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_DOCTORATE,
    ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_CONTINUING,
)
from osis_mail_template import MailTemplateMigration


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0129_valuated_experiences_evolutions_4'),
    ]

    SIC_OBJECT_TEMPLATE = {
        'en': '[OSIS] Requested documents for your application to UCLouvain ({admission_reference})',
        'fr-be': "[OSIS] Documents demandés pour votre candidature à l'UCLouvain ({admission_reference})",
    }

    SIC_CONTENT_TEMPLATE = {
        'en': '''<p>{salutation} {candidate_first_name} {candidate_last_name},</p>

                <p>
                    We have received your application for training {training_title} ({training_campus}) - 
                    {training_acronym} for the academic year {training_year} and we thank you for it.
                </p>

                <p>
                    After verification, we note that some elements are still missing.
                </p>

                <p>
                    In order to continue the admission procedure, some documents must be added to 
                    your online dossier through your online application dashboard: <a href="{admissions_link_front}">
                    {admissions_link_front}</a>
                </p>
                
                <div>
                    <p>
                        The following documents are mandatory to finalize your application and must be added immediately:
                    </p>
    
                    {requested_documents}
                </div>
                
                <div>
                    <p>
                        The following documents are mandatory to finalize your application but can be provided later, if you
                        don't have them yet:
                    </p>
                    
                    {later_requested_documents}
                </div>
                
                <div>
                    <p>
                         The following documents aren't mandatory and can be provided later if you don't have them yet:
                    </p>
                    
                    {later_requested_documents}
                </div>

                <p>
                    The documents must be provided by {request_deadline} at the latest, we strongly encourage you to 
                    respect this deadline. It is not necessary to send us the documents by mail. No follow-up will be 
                    given to documents sent by e-mail.
                </p>

                <p>
                    Yours sincerely.
                </p>

                <p>
                    The registration service.
                </p>        ''',
        'fr-be': '''<p>{salutation} {candidate_first_name} {candidate_last_name},</p>

        <p>
            Votre demande d'inscription au programme {training_title} ({training_campus}) - {training_acronym} pour
            l'année académique {training_year} nous est bien parvenue et nous vous en remercions.
        </p>

        <p>
            Après vérification, nous constatons qu'il manque encore certains éléments.
        </p>

        <p>
            Afin de pouvoir poursuivre la procédure d'admission, les documents suivants doivent être ajoutés 
            immédiatement à votre dossier en ligne obligatoirement via votre tableau de bord de votre demande en ligne : 
            <a href="{admissions_link_front}">{admissions_link_front}</a>
        </p>
        
        <div>
            <p>
                Les documents suivants sont requis pour finaliser votre candidature et doivent être ajoutés 
                immédiatement :
            </p>

            {requested_documents}
        </div>
        
        <div>
            <p>
                Les documents suivants sont requis pour finaliser votre candidature mais peuvent être fournis 
                ultérieurement, si vous ne les avez pas encore :
            </p>
            
            {later_requested_documents}
        </div>
        
        <div>
            <p>
                 Les documents suivants ne sont pas requis et peuvent être fournis ultérieurement, si vous ne les 
                 avez pas encore :
            </p>
            
            {later_requested_documents}
        </div>

        <p>
            Les documents sont à fournir pour le {request_deadline} au plus tard, nous vous invitons vivement à 
            respecter ce délai. Il n'est pas nécessaire de nous envoyer les documents par mail. Aucune suite ne sera 
            donnée aux documents envoyés par mail.
        </p>

        <p>
            Veuillez agréer, Madame, Monsieur, l'expression de nos salutations distinguées.
        </p>

        <p>
            Le Service des inscriptions.
        </p>
        ''',
    }

    FAC_OBJECT_TEMPLATE = {
        'en': '[OSIS] Requested documents for your application to UCLouvain ({admission_reference})',
        'fr-be': "[OSIS] Documents demandés pour votre candidature à l'UCLouvain ({admission_reference})",
    }

    FAC_CONTENT_TEMPLATE = {
        'en': '''<p>Dear Madam or Sir</p>

                <p>
                    We have received your application for training {training_title} ({training_campus}) - 
                    {training_acronym} for the academic year {training_year} and we thank you for it.
                </p>

                <p>
                    After verification, we note that some elements are still missing.
                </p>

                <p>
                    In order to continue the admission procedure, some documents must be added to 
                    your online dossier through your online application dashboard: <a href="{admissions_link_front}">
                    {admissions_link_front}</a>
                </p>
                
                <div>
                    <p>
                        The following documents are mandatory to finalize your application and must be added immediately:
                    </p>
    
                    {requested_documents}
                </div>
                
                <div>
                    <p>
                        The following documents are mandatory to finalize your application but can be provided later, if you
                        don't have them yet:
                    </p>
                    
                    {later_requested_documents}
                </div>
                
                <div>
                    <p>
                         The following documents aren't mandatory and can be provided later if you don't have them yet:
                    </p>
                    
                    {later_requested_documents}
                </div>

                <p>
                    The documents must be provided by {request_deadline} at the latest, we strongly encourage you to 
                    respect this deadline. It is not necessary to send us the documents by mail. No follow-up will be 
                    given to documents sent by e-mail.
                </p>

                <p>
                    Yours sincerely.
                </p>

                <p>
                    The {management_entity_name} ({management_entity_acronym}).
                </p>        ''',
        'fr-be': '''<p>Madame, Monsieur,</p>

        <p>
            Votre demande d'inscription au programme {training_title} ({training_campus}) - {training_acronym} pour
            l'année académique {training_year} nous est bien parvenue et nous vous en remercions.
        </p>

        <p>
            Après vérification, nous constatons qu'il manque encore certains éléments.
        </p>

        <div>
            <p>
                Les documents suivants sont requis pour finaliser votre candidature et doivent être ajoutés 
                immédiatement :
            </p>

            {requested_documents}
        </div>
        
        <div>
            <p>
                Les documents suivants sont requis pour finaliser votre candidature mais peuvent être fournis 
                ultérieurement, si vous ne les avez pas encore :
            </p>
            
            {later_requested_documents}
        </div>
        
        <div>
            <p>
                 Les documents suivants ne sont pas requis et peuvent être fournis ultérieurement, si vous ne les 
                 avez pas encore :
            </p>
            
            {later_requested_documents}
        </div>

        <p>
            Les documents sont à fournir pour le {request_deadline} au plus tard, nous vous invitons vivement à 
            respecter ce délai. Il n'est pas nécessaire de nous envoyer les documents par mail. Aucune suite ne sera 
            donnée aux documents envoyés par mail.
        </p>

        <p>
            Veuillez agréer, Madame, Monsieur, l'expression de nos salutations distinguées.
        </p>

        <p>
            La {management_entity_name} ({management_entity_acronym}).
        </p>
        ''',
    }

    operations = [
        MailTemplateMigration(
            ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_GENERAL,
            SIC_OBJECT_TEMPLATE,
            SIC_CONTENT_TEMPLATE,
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_GENERAL,
            FAC_OBJECT_TEMPLATE,
            FAC_CONTENT_TEMPLATE,
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_DOCTORATE,
            SIC_OBJECT_TEMPLATE,
            SIC_CONTENT_TEMPLATE,
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_DOCTORATE,
            FAC_OBJECT_TEMPLATE,
            FAC_CONTENT_TEMPLATE,
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_CONTINUING,
            FAC_OBJECT_TEMPLATE,
            FAC_CONTENT_TEMPLATE,
        ),
    ]
