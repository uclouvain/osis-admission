# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict, Tuple, List

from django.db import models
from django.utils.html import format_html

from base.models.utils.utils import ChoiceEnum
from osis_profile.models.epc_injection import TECHNICAL_ERRORS as CUREX_TECHNICAL_ERRORS

TECHNICAL_ERRORS = CUREX_TECHNICAL_ERRORS + [
    'MISSING_REQUIRED_OBJECT',
    'INVALID_BIRTHDATE',
]


class EPCInjectionStatus(ChoiceEnum):
    OK = "Injecté"
    ERROR = "Erreur"
    NO_SENT = "Pas encore envoyé dans EPC"
    PENDING = "En attente du retour d'EPC"
    OSIS_ERROR = "Erreur OSIS"

    @classmethod
    def blocking_statuses_for_experience(cls) -> List[str]:
        return [
            cls.OK.name,
            cls.PENDING.name,
        ]


class EPCInjectionType(ChoiceEnum):
    DEMANDE = "Demande"
    SIGNALETIQUE = "Signalétique"


class EPCInjection(models.Model):
    last_attempt_date = models.DateTimeField(null=True)
    last_response_date = models.DateTimeField(null=True)
    admission = models.ForeignKey(
        'admission.BaseAdmission',
        on_delete=models.CASCADE,
        related_name='epc_injection',
    )
    type = models.CharField(choices=EPCInjectionType.choices(), null=False, blank=True, default='', max_length=12)
    status = models.CharField(choices=EPCInjectionStatus.choices(), null=False, blank=True, default='', max_length=10)
    payload = models.JSONField(default=dict, blank=True)
    epc_responses = models.JSONField(default=list, blank=True)

    @property
    def last_response(self) -> Dict[str, str]:
        if self.epc_responses:
            return self.epc_responses[-1]

    @property
    def errors_messages(self) -> List[str]:
        messages = [message for _, message in self.experiences_errors]
        if self.classified_errors['technical_errors']:
            messages.append('Erreur technique')
        return messages

    @property
    def experiences_errors(self) -> List[Tuple[str, str]]:
        return self.classified_errors['curriculum_errors']

    @property
    def classified_errors(self) -> Dict[str, List[Tuple[str, str]]]:
        if self.last_response:
            errors = self.last_response.get('errors', []) or []
            return {
                'curriculum_errors': [
                    (error['osis_uuid'], error['message']) for error in errors if error['type'] not in TECHNICAL_ERRORS
                ],
                'technical_errors': [error['message'] for error in errors if error['type'] in TECHNICAL_ERRORS],
            }
        return {
            'curriculum_errors': [],
            'technical_errors': [],
        }

    @property
    def html_errors(self):
        li_elements = [f"<li>{error_message}</li>" for error_message in self.errors_messages]
        return format_html("<ul>\n" + "\n".join(li_elements) + "\n</ul>") if li_elements else ""
