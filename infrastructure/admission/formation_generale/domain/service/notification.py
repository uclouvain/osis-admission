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

from django.conf import settings
from django.shortcuts import resolve_url
from django.utils import translation
from django.utils.translation import gettext as _
from osis_async.models import AsyncTask
from osis_mail_template import generate_email
from osis_mail_template.utils import transform_html_to_text
from osis_notification.contrib.handlers import EmailNotificationHandler
from osis_notification.contrib.notification import EmailNotification

from admission.contrib.models import AdmissionTask
from admission.contrib.models.base import BaseAdmission, BaseAdmissionProxy
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.service.i_notification import INotification
from admission.infrastructure.admission.formation_generale.domain.service.formation import FormationGeneraleTranslator
from admission.infrastructure.parcours_doctoral.epreuve_confirmation.domain.service.notification import (
    send_mail_to_generic_email,
)
from admission.mail_templates import (
    ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL,
    ADMISSION_EMAIL_SEND_TO_FAC_AT_FAC_DECISION_GENERAL,
)
from admission.mail_templates.submission import ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL
from admission.utils import get_portal_admission_url, get_backoffice_admission_url, get_salutation_prefix
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
            common_tokens['salutation'] = get_salutation_prefix(
                person=admission.candidate,
                language=admission.candidate.language,
            )
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
            recipients=[admission.candidate],
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
            recipients=[admission.candidate],
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
