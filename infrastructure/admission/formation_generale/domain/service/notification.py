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
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.service.i_notification import INotification
from admission.infrastructure.admission.formation_generale.domain.service.formation import FormationGeneraleTranslator
from admission.mail_templates import ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL
from admission.mail_templates.submission import ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL
from base.models.person import Person


class Notification(INotification):
    @classmethod
    def get_common_tokens(cls, proposition: Proposition, candidat):
        """Return common tokens about a submission"""
        frontend_link = settings.ADMISSION_FRONTEND_LINK.format(
            context='general-education',
            uuid=proposition.entity_id.uuid,
        )
        formation_id = proposition.formation_id
        backend_link = "{}{}".format(
            settings.ADMISSION_BACKEND_LINK_PREFIX.rstrip('/'),
            resolve_url('admission:general-education', uuid=proposition.entity_id.uuid),
        )
        return {
            "candidate_first_name": candidat.first_name,
            "candidate_last_name": candidat.last_name,
            "training_title": FormationGeneraleTranslator().get_dto(formation_id.sigle, formation_id.annee).intitule,
            "admission_link_front": frontend_link,
            "admission_link_back": backend_link,
        }

    @classmethod
    def confirmer_soumission(cls, proposition: Proposition) -> None:
        # The candidate will be notified only when the proposition is confirmed
        if proposition.statut != ChoixStatutPropositionGenerale.CONFIRMEE:
            return

        admission = BaseAdmission.objects.select_related('candidate').get(uuid=proposition.entity_id.uuid)

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

        # Notifier le candidat via mail
        with translation.override(admission.candidate.language):
            common_tokens = cls.get_common_tokens(proposition, admission.candidate)
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
