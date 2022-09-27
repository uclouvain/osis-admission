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
from email.message import EmailMessage

from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from admission.ddd.doctorat.domain.model.doctorat import Doctorat
from admission.ddd.doctorat.domain.service.i_historique import IHistorique
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import PersonneConnueUclTranslator
from osis_history.utilities import add_history_entry

FORMATTED_EMAIL_FOR_HISTORY = """{sender_label} : {sender}
{recipient_label} : {recipient}
{cc}{subject_label} : {subject}

{message}"""


class Historique(IHistorique):
    @classmethod
    def historiser_message_au_doctorant(cls, doctorat: Doctorat, matricule_emetteur: str, message: EmailMessage):
        emetteur = PersonneConnueUclTranslator.get(matricule_emetteur)

        plain_text_content = ""
        for part in message.walk():
            # Mail payload is decoded to bytes then decode to utf8
            if part.get_content_type() == "text/plain":
                plain_text_content = part.get_payload(decode=True).decode(settings.DEFAULT_CHARSET)

        format_args = {
            'sender_label': _("Sender"),
            'recipient_label': _("Recipient"),
            'subject_label': _("Subject"),
            'sender': message.get("From"),
            'recipient': message.get("To"),
            'cc': "CC : {}\n".format(message.get("Cc")) if message.get("Cc") else '',
            'subject': message.get("Subject"),
            'message': plain_text_content,
        }
        with translation.override(settings.LANGUAGE_CODE_FR):
            message_fr = FORMATTED_EMAIL_FOR_HISTORY.format(**format_args)
        with translation.override(settings.LANGUAGE_CODE_EN):
            message_en = FORMATTED_EMAIL_FOR_HISTORY.format(**format_args)
        add_history_entry(
            doctorat.entity_id.uuid,
            message_fr,
            message_en,
            "{emetteur.prenom} {emetteur.nom}".format(emetteur=emetteur),
            tags=["doctorat", "message"],
        )
