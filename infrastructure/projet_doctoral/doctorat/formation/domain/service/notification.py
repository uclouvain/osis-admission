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
from typing import List, Union

from django.conf import settings
from django.shortcuts import resolve_url
from django.utils.functional import Promise, lazy
from django.utils.translation import get_language

from admission.contrib.models import DoctorateAdmission
from admission.contrib.models.doctorate import DoctorateProxy
from admission.ddd.projet_doctoral.doctorat.domain.model.doctorat import Doctorat
from admission.ddd.projet_doctoral.doctorat.formation.domain.model.activite import Activite
from admission.ddd.projet_doctoral.doctorat.formation.domain.service.i_notification import INotification
from admission.ddd.projet_doctoral.preparation.commands import UUID
from admission.ddd.projet_doctoral.preparation.domain.model._promoteur import PromoteurIdentity
from admission.mail_templates import ADMISSION_EMAIL_REFERENCE_PROMOTER_TRAININGS_SUBMITTED
from base.models.person import Person
from osis_mail_template import generate_email
from osis_notification.contrib.handlers import EmailNotificationHandler


class Notification(INotification):
    @classmethod
    def get_admission_link_front(cls, uuid: UUID, tab='') -> str:
        return settings.ADMISSION_FRONTEND_LINK.format(uuid=uuid) + tab

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
    def get_common_tokens(
        cls,
        doctorate: Union[DoctorateProxy, DoctorateAdmission],
    ) -> dict:
        """Return common tokens about a doctorate"""
        return {
            "student_first_name": doctorate.candidate.first_name,
            "student_last_name": doctorate.candidate.last_name,
            "doctorate_title": cls._get_doctorate_title_translation(doctorate),
            "admission_link_front": cls.get_admission_link_front(doctorate.uuid),
            "admission_link_front_training": cls.get_admission_link_front(doctorate.uuid, 'training'),
            "admission_link_back": "{}{}".format(
                settings.ADMISSION_BACKEND_LINK_PREFIX.rstrip('/'),
                resolve_url('admission:doctorate:project', uuid=doctorate.uuid),
            ),
            "admission_link_back_training": "{}{}".format(
                settings.ADMISSION_BACKEND_LINK_PREFIX.rstrip('/'),
                resolve_url('admission:doctorate:training', uuid=doctorate.uuid),
            ),
            "reference": doctorate.reference,
        }

    @classmethod
    def notifier_soumission_au_promoteur_de_reference(
        cls,
        doctorat: Doctorat,
        activites: List[Activite],
        promoteur_de_reference_id: PromoteurIdentity,
    ) -> None:
        doctorate: DoctorateProxy = DoctorateProxy.objects.get(uuid=doctorat.entity_id.uuid)
        common_tokens = cls.get_common_tokens(doctorate)
        promoteur = Person.objects.get(global_id=promoteur_de_reference_id.matricule)

        email_message = generate_email(
            ADMISSION_EMAIL_REFERENCE_PROMOTER_TRAININGS_SUBMITTED,
            promoteur.language,
            common_tokens,
            recipients=[promoteur],
        )
        EmailNotificationHandler.create(email_message, person=promoteur)
