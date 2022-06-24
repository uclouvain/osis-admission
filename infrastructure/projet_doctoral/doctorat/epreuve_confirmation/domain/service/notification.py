# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime
from typing import Optional, Union, Type
from uuid import UUID

from django.conf import settings
from django.conf.global_settings import DATE_FORMAT
from django.shortcuts import resolve_url
from django.utils import translation
from django.utils.functional import lazy, Promise
from django.utils.translation import get_language, gettext as _
from osis_async.models import AsyncTask
from osis_mail_template.utils import transform_html_to_text, generate_email
from osis_notification.contrib.notification import EmailNotification, WebNotification

from admission.auth.roles.cdd_manager import CddManager
from admission.contrib.models import AdmissionTask, DoctorateAdmission
from admission.contrib.models.doctorate import DoctorateProxy
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.domain.model.epreuve_confirmation import (
    EpreuveConfirmation,
)
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.domain.service.i_notification import INotification
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from admission.ddd.projet_doctoral.preparation.domain.model._financement import ChoixTypeFinancement, BourseRecherche
from admission.mail_templates import (
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT,
)
from base.forms.utils.datefield import DATE_FORMAT
from osis_notification.contrib.handlers import EmailNotificationHandler, WebNotificationHandler


class Notification(INotification):

    @classmethod
    def format_date(cls, date: Optional[datetime.date]) -> str:
        return datetime.date.strftime(date, DATE_FORMAT) if date else ''

    @classmethod
    def _get_doctorate_title_translation(cls, doctorate: Union[DoctorateProxy, DoctorateAdmission]) -> Promise:
        """Populate the translations of the doctorate title and lazy return them"""
        # Create a dict to cache the translations of the doctorate title
        doctorate_title = {
            settings.LANGUAGE_CODE_EN: doctorate.doctorate.title_english,
            settings.LANGUAGE_CODE_FR: doctorate.doctorate.title,
        }

        # Return a lazy proxy which, when evaluated to string, return the correct translation given the current language
        return lazy(lambda: doctorate_title[get_language()], str)()

    @classmethod
    def get_admission_link_back(cls, uuid: UUID, tab='project') -> str:
        return "{}{}".format(
            settings.ADMISSION_BACKEND_LINK_PREFIX.rstrip('/'),
            resolve_url('admission:doctorate:{}'.format(tab), uuid=uuid),
        )

    @classmethod
    def get_admission_link_front(cls, uuid: UUID, tab='') -> str:
        return settings.ADMISSION_FRONTEND_LINK.format(uuid=uuid) + tab

    @classmethod
    def get_common_tokens(
        cls,
        doctorate: Union[DoctorateProxy, DoctorateAdmission],
        confirmation_paper: Union[EpreuveConfirmationDTO, EpreuveConfirmation],
    ) -> dict:
        """Return common tokens about a doctorate"""
        financing_type = (
            BourseRecherche.get_value(doctorate.scholarship_grant)
            if doctorate.financing_type == ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name
            else ChoixTypeFinancement.get_value(doctorate.financing_type)
        )

        return {
            "student_first_name": doctorate.candidate.first_name,
            "student_last_name": doctorate.candidate.last_name,
            "doctorate_title": cls._get_doctorate_title_translation(doctorate),
            "admission_link_front": cls.get_admission_link_front(doctorate.uuid),
            "admission_link_back": cls.get_admission_link_back(doctorate.uuid),
            "confirmation_paper_link_front": cls.get_admission_link_front(doctorate.uuid, 'confirmation'),
            "confirmation_paper_link_back": cls.get_admission_link_back(doctorate.uuid, 'confirmation'),
            "confirmation_paper_date": cls.format_date(confirmation_paper.date),
            "confirmation_paper_deadline": cls.format_date(confirmation_paper.date_limite),
            "scholarship_grant_acronym": financing_type,
            "reference": doctorate.reference,
            "extension_request_proposed_date": confirmation_paper.demande_prolongation.nouvelle_echeance
            if confirmation_paper.demande_prolongation
            else '',
        }

    @classmethod
    def _send_notification_to_managers(cls, entity_id: Type[int], content: str, tokens: dict) -> None:
        cdd_managers = CddManager.objects.filter(
            entity_id=entity_id,
        ).select_related('person')

        for manager in cdd_managers:
            with translation.override(manager.person.language):
                web_notification = WebNotification(recipient=manager.person, content=str(content % tokens))
            WebNotificationHandler.create(web_notification)

    @classmethod
    def notifier_soumission(cls, epreuve_confirmation: EpreuveConfirmation) -> None:
        doctorate: DoctorateProxy = DoctorateProxy.objects.get(uuid=epreuve_confirmation.doctorat_id.uuid)
        common_tokens = cls.get_common_tokens(doctorate, epreuve_confirmation)

        # Notify the CDD managers > web notification
        cls._send_notification_to_managers(
            entity_id=doctorate.doctorate.management_entity_id,
            content=_(
                '<a href="%(confirmation_paper_link_back)s">%(reference)s</a> - '
                '%(student_first_name)s %(student_last_name)s submitted '
                'a date for the confirmation paper for %(doctorate_title)s'
            ),
            tokens=common_tokens,
        )

    @classmethod
    def notifier_nouvelle_echeance(cls, epreuve_confirmation: EpreuveConfirmation) -> None:
        doctorate: DoctorateProxy = DoctorateProxy.objects.get(uuid=epreuve_confirmation.doctorat_id.uuid)
        common_tokens = cls.get_common_tokens(doctorate, epreuve_confirmation)

        # Notify the CCD managers > web notification
        cls._send_notification_to_managers(
            entity_id=doctorate.doctorate.management_entity_id,
            content=_(
                '<a href="%(confirmation_paper_link_back)s">%(reference)s</a> - '
                '%(student_first_name)s %(student_last_name)s proposed a new deadline '
                '(%(extension_request_proposed_date)s) for the confirmation paper for %(doctorate_title)s'
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
        supervising_actor_emails = doctorate.supervision_group.actors.select_related('person').values_list(
            'person__email',
            flat=True,
        )

        student_email_message = EmailNotificationHandler.build(email_notification)
        student_email_message['Cc'] = ','.join(supervising_actor_emails)

        EmailNotificationHandler.create(student_email_message, person=doctorate.candidate)

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
        supervising_actor_emails = doctorate.supervision_group.actors.select_related('person').values_list(
            'person__email',
            flat=True,
        )

        email_message = EmailNotificationHandler.build(email_notification)
        email_message['Cc'] = ','.join(supervising_actor_emails)

        EmailNotificationHandler.create(email_message, person=doctorate.candidate)

    @classmethod
    def notifier_reussite_epreuve(cls, epreuve_confirmation: EpreuveConfirmation):
        doctorate = DoctorateProxy.objects.get(uuid=epreuve_confirmation.doctorat_id.uuid)

        # Create the async task to generate the success attestation
        task = AsyncTask.objects.create(
            name=_('Create the confirmation paper success attestation ({reference})')
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
