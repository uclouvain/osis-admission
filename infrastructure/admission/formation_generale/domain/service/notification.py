# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from email.message import EmailMessage
from typing import List, Dict

from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext as _
from osis_async.models import AsyncTask
from osis_mail_template import generate_email
from osis_mail_template.utils import transform_html_to_text
from osis_notification.contrib.handlers import EmailNotificationHandler
from osis_notification.contrib.notification import EmailNotification

from admission.contrib.models import AdmissionTask
from admission.contrib.models.base import BaseAdmission, BaseAdmissionProxy
from admission.ddd import MAIL_INSCRIPTION_DEFAUT
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
from admission.infrastructure.admission.formation_generale.domain.service.formation import FormationGeneraleTranslator
from admission.infrastructure.parcours_doctoral.epreuve_confirmation.domain.service.notification import (
    send_mail_to_generic_email,
)
from admission.mail_templates import (
    ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL,
    ADMISSION_EMAIL_SEND_TO_FAC_AT_FAC_DECISION_GENERAL,
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_GENERAL,
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_GENERAL,
)
from admission.mail_templates.submission import ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL
from admission.utils import (
    get_portal_admission_url,
    get_backoffice_admission_url,
    get_salutation_prefix,
    format_academic_year,
)
from base.models.person import Person


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
        }

    @classmethod
    def confirmer_soumission(cls, proposition: Proposition) -> None:
        # The candidate will be notified only when the proposition is confirmed
        if proposition.statut != ChoixStatutPropositionGenerale.CONFIRMEE:
            return

        admission = (
            BaseAdmissionProxy.objects.with_training_management_and_reference()
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
            recipients=[admission.candidate.email],
        )
        EmailNotificationHandler.create(email_message, person=admission.candidate)

    @classmethod
    def demande_complements(cls, proposition: Proposition, objet_message: str, corps_message: str) -> EmailMessage:
        # Notifier le candidat via mail
        candidate = Person.objects.get(global_id=proposition.matricule_candidat)

        email_notification = EmailNotification(
            recipient=candidate,
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
            BaseAdmissionProxy.objects.with_training_management_and_reference()
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
            recipients=[admission.candidate.email],
        )
        EmailNotificationHandler.create(email_message, person=admission.candidate)

        return email_message

    @classmethod
    def confirmer_envoi_a_fac_lors_de_la_decision_facultaire(cls, proposition: Proposition) -> EmailMessage:
        admission = (
            BaseAdmissionProxy.objects.with_training_management_and_reference()
            .select_related('candidate__country_of_citizenship')
            .get(uuid=proposition.entity_id.uuid)
        )

        faculty_email = 'mail-inscription-formation-a-developper@uclouvain.be'  # TODO get the right faculty email

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
            common_tokens['admission_link_back_for_uclouvain_documents'] = get_backoffice_admission_url(
                context='general-education',
                admission_uuid=proposition.entity_id.uuid,
                sub_namespace=':documents',
            )
            common_tokens['candidate_nationality_country'] = getattr(
                admission.candidate.country_of_citizenship,
                {
                    settings.LANGUAGE_CODE_FR: 'name',
                    settings.LANGUAGE_CODE_EN: 'name_en',
                }[current_language],
            )

            email_message = generate_email(
                ADMISSION_EMAIL_SEND_TO_FAC_AT_FAC_DECISION_GENERAL,
                current_language,
                common_tokens,
                recipients=[faculty_email],
            )

            send_mail_to_generic_email(email_message)

            return email_message

    @classmethod
    def _get_requested_documents_html_lists(
        cls,
        requested_documents: List[EmplacementDocument],
        requested_documents_dtos: List[EmplacementDocumentDTO],
    ):
        """
        Create an html list with the requested and submitted documents and an html list with the requested and not
        submitted documents.
        :param requested_documents: List of requested documents with the updated status
        :param requested_documents_dtos: List of requested documents dtos
        :return: a dict whose the keys are the documents statuses and the values, the html lists of documents grouped
        by tab.
        """
        updated_documents_by_identifier: Dict[str, EmplacementDocument] = {
            document.entity_id.identifiant: document for document in requested_documents
        }

        current_tab_by_status = {
            StatutEmplacementDocument.A_RECLAMER: None,
            StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION: None,
        }
        html_list_by_status = {
            StatutEmplacementDocument.A_RECLAMER: '',
            StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION: '',
        }

        for document_dto in requested_documents_dtos:
            updated_document = updated_documents_by_identifier.get(document_dto.identifiant)

            if updated_document and updated_document.statut in html_list_by_status:
                # Group the documents by tab
                if current_tab_by_status[updated_document.statut] != document_dto.onglet:
                    if current_tab_by_status[updated_document.statut] is not None:
                        html_list_by_status[updated_document.statut] += '</ul></li>'

                    # Add the tab name
                    html_list_by_status[updated_document.statut] += f'<li>{document_dto.nom_onglet_langue_candidat}<ul>'

                # Add the document name
                html_list_by_status[updated_document.statut] += f'<li>{document_dto.libelle_langue_candidat}</li>'

                current_tab_by_status[updated_document.statut] = document_dto.onglet

        for status in html_list_by_status:
            if html_list_by_status[status]:
                html_list_by_status[status] = f'<ul>{html_list_by_status[status]}</ul></li></ul>'

        return html_list_by_status

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

        html_list_by_status = cls._get_requested_documents_html_lists(liste_documents_reclames, liste_documents_dto)

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
            'enrolment_service_email': admission.training.enrollment_campus.email or MAIL_INSCRIPTION_DEFAUT,
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
