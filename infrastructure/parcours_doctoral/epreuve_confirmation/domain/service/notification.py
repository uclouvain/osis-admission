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
from email.header import decode_header, make_header
from email.message import EmailMessage
from typing import Optional, Union
from unittest.mock import Mock
from uuid import UUID

from django.conf import settings
from django.shortcuts import resolve_url
from django.utils import translation
from django.utils.functional import Promise, lazy
from django.utils.module_loading import import_string
from django.utils.translation import get_language, gettext as _

from admission.models import AdmissionTask, DoctorateAdmission, SupervisionActor
from admission.models.doctorate import DoctorateProxy
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixTypeFinancement
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.parcours_doctoral.epreuve_confirmation.domain.model.epreuve_confirmation import (
    EpreuveConfirmation,
)
from admission.ddd.parcours_doctoral.epreuve_confirmation.domain.service.i_notification import INotification
from admission.ddd.parcours_doctoral.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from admission.mail_templates import (
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE,
)
from admission.utils import get_doctoral_cdd_managers
from base.forms.utils.datefield import DATE_FORMAT
from osis_async.models import AsyncTask
from osis_common.messaging.message_config import create_receiver
from osis_mail_template.utils import generate_email, transform_html_to_text
from osis_notification.contrib.handlers import EmailNotificationHandler, WebNotificationHandler
from osis_notification.contrib.notification import EmailNotification, WebNotification


class Notification(INotification):
    ADRE_EMAIL = 'adre@uclouvain.be'
    ADRI_EMAIL = 'adri@uclouvain.be'

    @classmethod
    def format_date(cls, date: Optional[datetime.date]) -> str:
        return datetime.date.strftime(date, DATE_FORMAT) if date else ''

    @classmethod
    def _get_doctorate_title_translation(cls, doctorate: Union[DoctorateProxy, DoctorateAdmission]) -> Promise:
        """Populate the translations of the doctorate title and lazy return them"""
        # Create a dict to cache the translations of the doctorate title
        doctorate_title = {
            settings.LANGUAGE_CODE_EN: doctorate.training.title_english,
            settings.LANGUAGE_CODE_FR: doctorate.training.title,
        }

        # Return a lazy proxy which, when evaluated to string, return the correct translation given the current language
        return lazy(lambda: doctorate_title[get_language()], str)()

    @classmethod
    def get_admission_link_back(cls, uuid: UUID, tab='project') -> str:
        return "{}{}".format(
            settings.ADMISSION_BACKEND_LINK_PREFIX,
            resolve_url('admission:doctorate:{}'.format(tab), uuid=uuid),
        )

    @classmethod
    def get_admission_link_front(cls, uuid: UUID, tab='') -> str:
        return settings.ADMISSION_FRONTEND_LINK.format(context='doctorate', uuid=uuid) + tab

    @classmethod
    def get_common_tokens(
        cls,
        doctorate: Union[DoctorateProxy, DoctorateAdmission],
        confirmation_paper: Union[EpreuveConfirmationDTO, EpreuveConfirmation],
    ) -> dict:
        """Return common tokens about a doctorate"""
        financing_type = (
            (
                str(doctorate.international_scholarship)
                if doctorate.international_scholarship_id
                else doctorate.other_international_scholarship
            )
            if doctorate.financing_type == ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name
            else ChoixTypeFinancement.get_value(doctorate.financing_type)
        )

        return {
            "student_first_name": doctorate.candidate.first_name,
            "student_last_name": doctorate.candidate.last_name,
            "training_title": cls._get_doctorate_title_translation(doctorate),
            "admission_link_front": cls.get_admission_link_front(doctorate.uuid),
            "admission_link_back": cls.get_admission_link_back(doctorate.uuid),
            "confirmation_paper_link_front": cls.get_admission_link_front(doctorate.uuid, 'confirmation'),
            "confirmation_paper_link_back": cls.get_admission_link_back(doctorate.uuid, 'confirmation'),
            "confirmation_paper_date": cls.format_date(confirmation_paper.date),
            "confirmation_paper_deadline": cls.format_date(confirmation_paper.date_limite),
            "scholarship_grant_acronym": financing_type,
            "reference": doctorate.reference,
            "extension_request_proposed_date": cls.format_date(
                confirmation_paper.demande_prolongation.nouvelle_echeance
            )
            if confirmation_paper.demande_prolongation
            else '',
        }

    @classmethod
    def _send_notification_to_managers(cls, education_group_id: int, content: str, tokens: dict) -> None:
        for manager in get_doctoral_cdd_managers(education_group_id):
            with translation.override(manager.language):
                web_notification = WebNotification(recipient=manager, content=str(content % tokens))
            WebNotificationHandler.create(web_notification)

    @classmethod
    def notifier_soumission(cls, epreuve_confirmation: EpreuveConfirmation) -> None:
        doctorate: DoctorateProxy = DoctorateProxy.objects.get(uuid=epreuve_confirmation.doctorat_id.uuid)
        common_tokens = cls.get_common_tokens(doctorate, epreuve_confirmation)

        if doctorate.post_enrolment_status == ChoixStatutDoctorat.SUBMITTED_CONFIRMATION.name:
            # Already submitted at least once
            manager_notification_content = _(
                '<a href="%(confirmation_paper_link_back)s">%(reference)s</a> - '
                '%(student_first_name)s %(student_last_name)s submitted new data '
                'for the confirmation paper for %(training_title)s'
            )

        else:
            # First submission
            manager_notification_content = _(
                '<a href="%(confirmation_paper_link_back)s">%(reference)s</a> - '
                '%(student_first_name)s %(student_last_name)s submitted data '
                'for the first time for the confirmation paper for %(training_title)s'
            )

            # Notify ADRE : email
            email_message = generate_email(
                ADMISSION_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE,
                settings.LANGUAGE_CODE,
                common_tokens,
                recipients=[cls.ADRE_EMAIL],
            )
            send_mail_to_generic_email(message=email_message)

        # Notify the CDD managers > web notification
        cls._send_notification_to_managers(
            education_group_id=doctorate.training.education_group_id,
            content=manager_notification_content,
            tokens=common_tokens,
        )

    @classmethod
    def notifier_completion_par_promoteur(cls, epreuve_confirmation: EpreuveConfirmation) -> None:
        doctorate: DoctorateProxy = DoctorateProxy.objects.get(uuid=epreuve_confirmation.doctorat_id.uuid)
        common_tokens = cls.get_common_tokens(doctorate, epreuve_confirmation)

        # Notify the CDD managers > web notification
        cls._send_notification_to_managers(
            education_group_id=doctorate.training.education_group_id,
            content=_(
                '<a href="%(confirmation_paper_link_back)s">%(reference)s</a> - '
                'A promoter submitted documents related to the confirmation paper of '
                '%(student_first_name)s %(student_last_name)s for %(training_title)s'
            ),
            tokens=common_tokens,
        )

    @classmethod
    def notifier_nouvelle_echeance(cls, epreuve_confirmation: EpreuveConfirmation) -> None:
        doctorate: DoctorateProxy = DoctorateProxy.objects.get(uuid=epreuve_confirmation.doctorat_id.uuid)
        common_tokens = cls.get_common_tokens(doctorate, epreuve_confirmation)

        # Notify the CCD managers > web notification
        cls._send_notification_to_managers(
            education_group_id=doctorate.training.education_group_id,
            content=_(
                '<a href="%(confirmation_paper_link_back)s">%(reference)s</a> - '
                '%(student_first_name)s %(student_last_name)s proposed a new deadline '
                '(%(extension_request_proposed_date)s) for the confirmation paper for %(training_title)s'
            ),
            tokens=common_tokens,
        )

    @classmethod
    def notifier_echec_epreuve(
        cls,
        epreuve_confirmation: EpreuveConfirmation,
        sujet_notification_candidat: str,
        message_notification_candidat: str,
    ) -> None:
        doctorate: DoctorateProxy = DoctorateProxy.objects.get(uuid=epreuve_confirmation.doctorat_id.uuid)

        email_notification = EmailNotification(
            recipient=doctorate.candidate,
            subject=sujet_notification_candidat,
            html_content=message_notification_candidat,
            plain_text_content=transform_html_to_text(message_notification_candidat),
        )

        # Notify the promoters and the ca members > email (cc)
        actors = SupervisionActor.objects.filter(process_id=doctorate.supervision_group_id).select_related('person')

        student_email_message = EmailNotificationHandler.build(email_notification)
        student_email_message['Cc'] = ','.join([cls._format_email(a) for a in actors])

        EmailNotificationHandler.create(student_email_message, person=doctorate.candidate)

        common_tokens = cls.get_common_tokens(doctorate, epreuve_confirmation)

        # Notify ADRE > email
        adre_email_message = generate_email(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE,
            settings.LANGUAGE_CODE,
            common_tokens,
            recipients=[cls.ADRE_EMAIL],
        )
        send_mail_to_generic_email(adre_email_message)

        # Notify ADRI > email
        adri_email_message = generate_email(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI,
            settings.LANGUAGE_CODE,
            common_tokens,
            recipients=[cls.ADRI_EMAIL],
        )
        send_mail_to_generic_email(adri_email_message)

    @classmethod
    def notifier_repassage_epreuve(
        cls,
        epreuve_confirmation: EpreuveConfirmation,
        sujet_notification_candidat: str,
        message_notification_candidat: str,
    ) -> None:
        doctorate: DoctorateProxy = DoctorateProxy.objects.get(uuid=epreuve_confirmation.doctorat_id.uuid)

        email_notification = EmailNotification(
            recipient=doctorate.candidate,
            subject=sujet_notification_candidat,
            html_content=message_notification_candidat,
            plain_text_content=transform_html_to_text(message_notification_candidat),
        )

        # Notify the promoters and the ca members > email (cc)
        actors = SupervisionActor.objects.filter(process_id=doctorate.supervision_group_id).select_related('person')

        email_message = EmailNotificationHandler.build(email_notification)
        email_message['Cc'] = ','.join([cls._format_email(a) for a in actors])

        EmailNotificationHandler.create(email_message, person=doctorate.candidate)

        common_tokens = cls.get_common_tokens(doctorate, epreuve_confirmation)

        # Notify ADRE > email
        adre_email_message = generate_email(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE,
            settings.LANGUAGE_CODE,
            common_tokens,
            recipients=[cls.ADRE_EMAIL],
        )
        send_mail_to_generic_email(adre_email_message)

        # Notify ADRI > email
        adri_email_message = generate_email(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI,
            settings.LANGUAGE_CODE,
            common_tokens,
            recipients=[cls.ADRI_EMAIL],
        )

        send_mail_to_generic_email(adri_email_message)

    @classmethod
    def notifier_reussite_epreuve(cls, epreuve_confirmation: EpreuveConfirmation):
        doctorate = DoctorateProxy.objects.get(uuid=epreuve_confirmation.doctorat_id.uuid)

        # Create the async task to generate the success attestation
        task = AsyncTask.objects.create(
            name=_('Create the confirmation paper success attestation (%(reference)s)')
            % {'reference': doctorate.reference},
            description=_('Create the confirmation paper success attestation as PDF'),
            person=doctorate.candidate,
            time_to_live=5,
        )
        AdmissionTask.objects.create(
            task=task,
            admission=doctorate,
            type=AdmissionTask.TaskType.CONFIRMATION_SUCCESS.name,
        )

        common_tokens = cls.get_common_tokens(doctorate, epreuve_confirmation)

        # Notify the student > email
        student_email_message = generate_email(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT,
            doctorate.candidate.language,
            common_tokens,
            recipients=[doctorate.candidate.email],
        )
        EmailNotificationHandler.create(student_email_message, person=doctorate.candidate)

        # Notify ADRE > email
        adre_email_message = generate_email(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE,
            settings.LANGUAGE_CODE,
            common_tokens,
            recipients=[cls.ADRE_EMAIL],
        )
        send_mail_to_generic_email(adre_email_message)

        # Notify ADRI > email
        adri_email_message = generate_email(
            ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI,
            settings.LANGUAGE_CODE,
            common_tokens,
            recipients=[cls.ADRI_EMAIL],
        )
        send_mail_to_generic_email(adri_email_message)

    @classmethod
    def _format_email(cls, actor: SupervisionActor):
        return "{a.first_name} {a.last_name} <{a.email}>".format(a=actor)


def send_mail_to_generic_email(message: EmailMessage):
    html_content = ''
    plain_text_content = ''

    for part in message.walk():
        if part.get_content_type() == "text/html":
            html_content = part.get_payload(decode=True).decode(settings.DEFAULT_CHARSET)
        elif part.get_content_type() == "text/plain":
            plain_text_content = part.get_payload(decode=True).decode(settings.DEFAULT_CHARSET)

    cc = message.get("Cc")
    if cc:
        cc = [Mock(email=cc_email) for cc_email in cc.split(',')]

    for mail_sender_class in settings.MAIL_SENDER_CLASSES:
        MailSenderClass = import_string(mail_sender_class)
        mail_sender = MailSenderClass(
            receivers=[
                create_receiver(
                    receiver_person_id=None,
                    receiver_email=message['To'],
                    receiver_lang=settings.LANGUAGE_CODE,
                )
            ],
            reference=None,
            connected_user=None,
            subject=make_header(decode_header(message.get("subject"))),
            message=plain_text_content,
            html_message=html_content,
            attachment=None,
            from_email=message['From'],
            cc=cc,
        )
        mail_sender.send_mail()
