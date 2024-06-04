# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime
from email.message import EmailMessage
from typing import List, Dict, Optional

from django.conf import settings
from django.utils import translation, formats
from django.utils.translation import gettext as _
from osis_async.models import AsyncTask

from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.infrastructure.utils import get_requested_documents_html_lists
from osis_document.api.utils import get_remote_token, get_remote_tokens
from osis_document.utils import get_file_url
from osis_mail_template import generate_email
from osis_mail_template.utils import transform_html_to_text
from osis_notification.contrib.handlers import EmailNotificationHandler
from osis_notification.contrib.notification import EmailNotification

from admission.contrib.models import AdmissionTask, GeneralEducationAdmission
from admission.contrib.models.base import BaseAdmission
from admission.ddd import MAIL_INSCRIPTION_DEFAUT, MAIL_VERIFICATEUR_CURSUS
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.emplacement_document import StatutEmplacementDocument
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.service.i_notification import INotification
from admission.ddd.admission.formation_generale.dtos import PropositionDTO
from admission.ddd.admission.shared_kernel.email_destinataire.domain.validator.exceptions import (
    InformationsDestinatairePasTrouvee,
)
from admission.ddd.admission.shared_kernel.email_destinataire.repository.i_email_destinataire import (
    IEmailDestinataireRepository,
)
from admission.infrastructure.admission.formation_generale.domain.service.formation import FormationGeneraleTranslator
from admission.mail_templates import (
    ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL,
    ADMISSION_EMAIL_SEND_TO_FAC_AT_FAC_DECISION_GENERAL,
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_GENERAL,
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_GENERAL,
)
from admission.mail_templates.checklist import (
    ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CANDIDATE,
    ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CHECKERS,
    EMAIL_TEMPLATE_ENROLLMENT_AUTHORIZATION_DOCUMENT_URL_TOKEN,
    EMAIL_TEMPLATE_VISA_APPLICATION_DOCUMENT_URL_TOKEN,
)
from admission.mail_templates.submission import ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL
from admission.utils import (
    get_portal_admission_url,
    get_backoffice_admission_url,
    get_salutation_prefix,
    get_portal_admission_list_url,
)
from base.models.person import Person
from base.utils.utils import format_academic_year

ONE_YEAR_SECONDS = 366 * 24 * 60 * 60
MOIS_DEBUT_TRAITEMENT_INSCRIPTION = 7
EMAIL_TEMPLATE_DOCUMENT_URL_TOKEN = 'SERA_AUTOMATIQUEMENT_REMPLACE_PAR_LE_LIEN'


class NotificationException(Exception):
    pass


class Notification(INotification):
    @classmethod
    def get_common_tokens(cls, proposition: Proposition, candidat):
        """Return common tokens about a submission"""
        formation_id = proposition.formation_id
        return {
            "candidate_first_name": candidat.first_name,
            "candidate_last_name": candidat.last_name,
            "training_title": FormationGeneraleTranslator().get_dto(formation_id.sigle, formation_id.annee).intitule,
            "admission_link_front": get_portal_admission_url(
                context='general-education',
                admission_uuid=proposition.entity_id.uuid,
            ),
            "admission_link_back": get_backoffice_admission_url(
                context='general-education',
                admission_uuid=proposition.entity_id.uuid,
            ),
            'admissions_link_front': get_portal_admission_list_url(),
        }

    @classmethod
    def confirmer_soumission(cls, proposition: Proposition) -> None:
        # The candidate will be notified only when the proposition is confirmed
        if proposition.statut != ChoixStatutPropositionGenerale.CONFIRMEE:
            return

        admission = (
            BaseAdmission.objects.with_training_management_and_reference()
            .select_related('candidate')
            .get(uuid=proposition.entity_id.uuid)
        )

        # Create the async task to generate the pdf recap
        task = AsyncTask.objects.create(
            name=_('Recap of the proposition %(reference)s') % {'reference': proposition.reference},
            description=_('Create the recap of the proposition'),
            person=admission.candidate,
        )
        AdmissionTask.objects.create(
            task=task,
            admission=admission,
            type=AdmissionTask.TaskType.GENERAL_RECAP.name,
        )

        # Create the async task to merge each document field of the proposition into one PDF
        task = AsyncTask.objects.create(
            name=_('Document merging of the proposition %(reference)s') % {'reference': proposition.reference},
            description=_('Merging of each document field of the proposition into one PDF'),
            person=admission.candidate,
        )
        AdmissionTask.objects.create(
            task=task,
            admission=admission,
            type=AdmissionTask.TaskType.GENERAL_MERGE.name,
        )

        # Notifier le candidat via mail
        with translation.override(admission.candidate.language):
            common_tokens = cls.get_common_tokens(proposition, admission.candidate)
            common_tokens['admission_reference'] = admission.formatted_reference
            common_tokens['salutation'] = get_salutation_prefix(person=admission.candidate)
            common_tokens['payment_sentence'] = (
                "<p>{}</p>".format(_('Application fees where also received.'))
                if proposition.checklist_actuelle.frais_dossier.statut == ChoixStatutChecklist.SYST_REUSSITE
                else ''
            )
            common_tokens['late_enrolment_sentence'] = (
                "<p><strong>{}</strong></p>".format(
                    _(
                        'We would like to draw your attention to the fact that you have submitted a late application. '
                        'The admission panel reserves the right to accept or refuse this application on the basis of '
                        'educational requirements.'
                    )
                )
                if proposition.est_inscription_tardive
                else ''
            )
            common_tokens['enrolment_sentence'] = (
                (
                    "<p>{}</p>".format(
                        _(
                            'For your information, applications for the %(academic_year)s academic year will be '
                            'processed from %(start_date)s.'
                        )
                    )
                )
                % {
                    'academic_year': format_academic_year(proposition.annee_calculee),
                    'start_date': formats.date_format(
                        datetime.date(proposition.annee_calculee, MOIS_DEBUT_TRAITEMENT_INSCRIPTION, 1),
                        'F Y',
                    ),
                }
                if proposition.type_demande == TypeDemande.INSCRIPTION
                else ''
            )
            common_tokens['training_acronym'] = proposition.formation_id.sigle
            common_tokens['recap_link'] = (
                get_portal_admission_url(
                    context='general-education',
                    admission_uuid=proposition.entity_id.uuid,
                )
                + 'pdf-recap'
            )

        email_message = generate_email(
            ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL,
            admission.candidate.language,
            common_tokens,
            recipients=[admission.candidate.private_email],
        )
        EmailNotificationHandler.create(email_message, person=admission.candidate)

    @classmethod
    def demande_complements(cls, proposition: Proposition, objet_message: str, corps_message: str) -> EmailMessage:
        # Notifier le candidat via mail
        candidate = Person.objects.get(global_id=proposition.matricule_candidat)

        email_notification = EmailNotification(
            recipient=candidate.private_email,
            subject=objet_message,
            html_content=corps_message,
            plain_text_content=transform_html_to_text(corps_message),
        )

        candidate_email_message = EmailNotificationHandler.build(email_notification)
        EmailNotificationHandler.create(candidate_email_message, person=candidate)

        return candidate_email_message

    @classmethod
    def demande_paiement_frais_dossier(cls, proposition: Proposition) -> EmailMessage:
        admission = (
            BaseAdmission.objects.with_training_management_and_reference()
            .select_related('candidate')
            .get(uuid=proposition.entity_id.uuid)
        )

        # Notifier le candidat via mail
        with translation.override(admission.candidate.language):
            common_tokens = cls.get_common_tokens(proposition, admission.candidate)
            common_tokens['admission_reference'] = admission.formatted_reference

        email_message = generate_email(
            ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL,
            admission.candidate.language,
            common_tokens,
            recipients=[admission.candidate.private_email],
        )
        EmailNotificationHandler.create(email_message, person=admission.candidate)

        return email_message

    @classmethod
    def confirmer_envoi_a_fac_lors_de_la_decision_facultaire(
        cls,
        proposition: Proposition,
        email_destinataire_repository: IEmailDestinataireRepository,
    ) -> Optional[EmailMessage]:
        admission: BaseAdmission = (
            BaseAdmission.objects.with_training_management_and_reference()
            .select_related('candidate__country_of_citizenship', 'training__enrollment_campus')
            .get(uuid=proposition.entity_id.uuid)
        )

        try:
            program_email = email_destinataire_repository.get_informations_destinataire_dto(
                sigle_programme=proposition.formation_id.sigle,
                annee=proposition.annee_calculee,
                pour_premiere_annee=proposition.premiere_annee_de_bachelier,
            )
        except InformationsDestinatairePasTrouvee:
            return

        current_language = settings.LANGUAGE_CODE

        with translation.override(current_language):
            common_tokens = cls.get_common_tokens(proposition, admission.candidate)
            common_tokens['admission_reference'] = admission.formatted_reference
            common_tokens['admission_link_back_for_fac_approval_checklist'] = get_backoffice_admission_url(
                context='general-education',
                admission_uuid=proposition.entity_id.uuid,
                sub_namespace=':checklist',
                url_suffix='#decision_facultaire',
            )
            common_tokens['candidate_nationality_country'] = getattr(
                admission.candidate.country_of_citizenship,
                {
                    settings.LANGUAGE_CODE_FR: 'name',
                    settings.LANGUAGE_CODE_EN: 'name_en',
                }[current_language],
            )
            common_tokens['training_acronym'] = admission.training.acronym
            common_tokens[
                'training_enrollment_campus_email'
            ] = admission.training.enrollment_campus.sic_enrollment_email

            email_message = generate_email(
                ADMISSION_EMAIL_SEND_TO_FAC_AT_FAC_DECISION_GENERAL,
                current_language,
                common_tokens,
                recipients=[program_email.email],
            )

            EmailNotificationHandler.create(email_message, person=None)

            return email_message

    @classmethod
    def confirmer_reception_documents_envoyes_par_candidat(
        cls,
        proposition: PropositionDTO,
        liste_documents_reclames: List[EmplacementDocument],
        liste_documents_dto: List[EmplacementDocumentDTO],
    ):
        admission: BaseAdmission = BaseAdmission.objects.select_related(
            'candidate',
            'training__enrollment_campus',
        ).get(uuid=proposition.uuid)

        html_list_by_status = get_requested_documents_html_lists(liste_documents_reclames, liste_documents_dto)

        tokens = {
            'admission_reference': proposition.reference,
            'candidate_first_name': proposition.prenom_candidat,
            'candidate_last_name': proposition.nom_candidat,
            'salutation': get_salutation_prefix(person=admission.candidate),
            'training_title': admission.training.title
            if admission.candidate.language == settings.LANGUAGE_CODE_FR
            else admission.training.title_english,
            'training_acronym': proposition.formation.sigle,
            'training_campus': proposition.formation.campus,
            'requested_submitted_documents': html_list_by_status[StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION],
            'requested_not_submitted_documents': html_list_by_status[StatutEmplacementDocument.A_RECLAMER],
            'enrolment_service_email': admission.training.enrollment_campus.sic_enrollment_email
            or MAIL_INSCRIPTION_DEFAUT,
            'training_year': format_academic_year(proposition.annee_calculee),
            'admission_link_front': get_portal_admission_url('general-education', proposition.uuid),
            'admission_link_back': get_backoffice_admission_url('general-education', proposition.uuid),
        }

        email_message = generate_email(
            ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_GENERAL
            if html_list_by_status[StatutEmplacementDocument.A_RECLAMER]
            else ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_GENERAL,
            admission.candidate.language,
            tokens,
            recipients=[admission.candidate.private_email],
        )
        EmailNotificationHandler.create(email_message, person=admission.candidate)

        # Create the async task to create the folder analysis containing the submitted documents
        task = AsyncTask.objects.create(
            name=_('Folder analysis of the proposition %(reference)s') % {'reference': admission.reference},
            description=_(
                'Create the folder analysis of the proposition containing the requested documents that the '
                'candidate submitted.',
            ),
            person=admission.candidate,
        )
        AdmissionTask.objects.create(
            task=task,
            admission=admission,
            type=AdmissionTask.TaskType.GENERAL_FOLDER.name,
        )

    @classmethod
    def refuser_proposition_par_sic(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> Optional[EmailMessage]:
        if not objet_message or not corps_message:
            return None

        candidate = Person.objects.get(global_id=proposition.matricule_candidat)

        document_uuid = (
            GeneralEducationAdmission.objects.filter(uuid=proposition.entity_id.uuid).values('sic_refusal_certificate')
        )[0]['sic_refusal_certificate'][0]
        token = get_remote_token(document_uuid, custom_ttl=ONE_YEAR_SECONDS)
        document_url = get_file_url(token)
        corps_message = corps_message.replace(EMAIL_TEMPLATE_DOCUMENT_URL_TOKEN, document_url)

        email_notification = EmailNotification(
            recipient=candidate.private_email,
            subject=objet_message,
            html_content=corps_message,
            plain_text_content=transform_html_to_text(corps_message),
        )

        candidate_email_message = EmailNotificationHandler.build(email_notification)
        EmailNotificationHandler.create(candidate_email_message, person=candidate)

        return candidate_email_message

    @classmethod
    def accepter_proposition_par_sic(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> EmailMessage:
        candidate = Person.objects.get(global_id=proposition.matricule_candidat)

        admission = (
            GeneralEducationAdmission.objects.filter(uuid=proposition.entity_id.uuid)
            .only(
                'sic_approval_certificate',
                'sic_annexe_approval_certificate',
            )
            .first()
        )

        sic_annexe_approval_certificate_url = ''
        sic_approval_certificate_url = ''

        document_uuids = {
            field: str(getattr(admission, field)[0]) if getattr(admission, field) else ''
            for field in ['sic_annexe_approval_certificate', 'sic_approval_certificate']
        }

        document_uuids_list = [document for document in document_uuids.values() if document]

        if document_uuids_list:
            document_tokens = get_remote_tokens(document_uuids_list, custom_ttl=ONE_YEAR_SECONDS)

            if document_tokens:
                if document_uuids['sic_approval_certificate'] and document_tokens.get(
                    document_uuids['sic_approval_certificate']
                ):
                    sic_approval_certificate_url = get_file_url(
                        document_tokens[document_uuids['sic_approval_certificate']]
                    )
                if document_uuids['sic_annexe_approval_certificate'] and document_tokens.get(
                    document_uuids['sic_annexe_approval_certificate']
                ):
                    sic_annexe_approval_certificate_url = get_file_url(
                        document_tokens[document_uuids['sic_annexe_approval_certificate']]
                    )

        corps_message = corps_message.replace(
            EMAIL_TEMPLATE_ENROLLMENT_AUTHORIZATION_DOCUMENT_URL_TOKEN,
            sic_approval_certificate_url,
        )
        corps_message = corps_message.replace(
            EMAIL_TEMPLATE_VISA_APPLICATION_DOCUMENT_URL_TOKEN,
            sic_annexe_approval_certificate_url,
        )

        email_notification = EmailNotification(
            recipient=candidate.private_email,
            subject=objet_message,
            html_content=corps_message,
            plain_text_content=transform_html_to_text(corps_message),
        )

        candidate_email_message = EmailNotificationHandler.build(email_notification)
        EmailNotificationHandler.create(candidate_email_message, person=candidate)

        return candidate_email_message

    @classmethod
    def demande_verification_titre_acces(cls, proposition: Proposition) -> EmailMessage:
        admission: BaseAdmission = (
            BaseAdmission.objects.with_training_management_and_reference()
            .select_related('candidate__country_of_citizenship', 'training')
            .get(uuid=proposition.entity_id.uuid)
        )

        # Notifier le vérificateur par mail
        current_language = settings.LANGUAGE_CODE
        with translation.override(current_language):
            tokens = {
                'admission_reference': admission.formatted_reference,
                'candidate_first_name': admission.candidate.first_name,
                'candidate_last_name': admission.candidate.last_name,
                'candidate_nationality_country': {
                    settings.LANGUAGE_CODE_FR: admission.candidate.country_of_citizenship.name,
                    settings.LANGUAGE_CODE_EN: admission.candidate.country_of_citizenship.name_en,
                }[current_language],
                'training_title': {
                    settings.LANGUAGE_CODE_FR: admission.training.title,
                    settings.LANGUAGE_CODE_EN: admission.training.title_english,
                }[current_language],
                'training_acronym': admission.training.acronym,
                'training_year': format_academic_year(proposition.annee_calculee),
                'admission_link_front': get_portal_admission_url('general-education', str(admission.uuid)),
                'admission_link_back': get_backoffice_admission_url('general-education', str(admission.uuid)),
            }

            email_message = generate_email(
                ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CHECKERS,
                admission.candidate.language,
                tokens,
                recipients=[MAIL_VERIFICATEUR_CURSUS],
            )

            EmailNotificationHandler.create(email_message, person=None)

            return email_message

    @classmethod
    def informer_candidat_verification_parcours_en_cours(cls, proposition: Proposition) -> EmailMessage:
        admission: BaseAdmission = (
            BaseAdmission.objects.with_training_management_and_reference()
            .select_related('candidate', 'training')
            .get(uuid=proposition.entity_id.uuid)
        )

        # Notifier le candidat par mail
        with translation.override(admission.candidate.language):
            tokens = {
                'admission_reference': admission.formatted_reference,
                'candidate_first_name': admission.candidate.first_name,
                'candidate_last_name': admission.candidate.last_name,
                'training_title': {
                    settings.LANGUAGE_CODE_FR: admission.training.title,
                    settings.LANGUAGE_CODE_EN: admission.training.title_english,
                }[admission.candidate.language],
                'training_acronym': admission.training.acronym,
                'training_campus': admission.teaching_campus,
                'training_year': format_academic_year(proposition.annee_calculee),
                'admission_link_front': get_portal_admission_url('general-education', str(admission.uuid)),
                'admission_link_back': get_backoffice_admission_url('general-education', str(admission.uuid)),
            }

            email_message = generate_email(
                ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CANDIDATE,
                admission.candidate.language,
                tokens,
                recipients=[admission.candidate.private_email],
            )

            EmailNotificationHandler.create(email_message, person=admission.candidate)

            return email_message

    @classmethod
    def notifier_candidat_derogation_financabilite(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> EmailMessage:
        candidate = Person.objects.get(global_id=proposition.matricule_candidat)

        email_notification = EmailNotification(
            recipient=candidate.private_email,
            subject=objet_message,
            html_content=corps_message,
            plain_text_content=transform_html_to_text(corps_message),
        )

        candidate_email_message = EmailNotificationHandler.build(email_notification)
        EmailNotificationHandler.create(candidate_email_message, person=candidate)

        return candidate_email_message
