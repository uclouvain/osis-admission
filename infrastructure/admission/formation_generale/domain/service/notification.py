# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf import settings
from django.shortcuts import resolve_url
from django.utils import translation

from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.service.i_notification import INotification
from admission.infrastructure.admission.formation_generale.domain.service.formation import FormationGeneraleTranslator
from admission.mail_templates.submission import ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL
from base.models.person import Person
from osis_mail_template import generate_email
from osis_notification.contrib.handlers import EmailNotificationHandler


class Notification(INotification):
    @classmethod
    def get_common_tokens(cls, proposition: Proposition, candidat):
        """Return common tokens about a submission"""
        frontend_link = settings.ADMISSION_FRONTEND_LINK.format(
            context='continuing-education',
            uuid=proposition.entity_id.uuid,
        )
        formation_id = proposition.formation_id
        backend_link = "{}{}".format(
            settings.ADMISSION_BACKEND_LINK_PREFIX.rstrip('/'),
            resolve_url('admission:continuing-education', uuid=proposition.entity_id.uuid),
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
        candidat = Person.objects.get(global_id=proposition.matricule_candidat)

        # Notifier le doctorant via mail
        with translation.override(candidat.language):
            common_tokens = cls.get_common_tokens(proposition, candidat)
        email_message = generate_email(
            ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL,
            candidat.language,
            common_tokens,
            recipients=[candidat],
        )
        EmailNotificationHandler.create(email_message, person=candidat)
