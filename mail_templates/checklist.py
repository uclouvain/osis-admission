# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import gettext_lazy as _
from osis_mail_template import Token, templates

from .tokens import GENERAL_ADMISSION_TAG, admission_common_tokens

__all__ = [
    'ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL',
    'ADMISSION_EMAIL_SEND_TO_FAC_AT_FAC_DECISION_GENERAL',
]


CHECKLIST_TOKENS = admission_common_tokens + [
    Token(
        name='admission_reference',
        description=_('Reference of the admission'),
        example='L-ESPO24-100.102',
    ),
]

ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL = 'osis-admission-request-application-fees-general'
templates.register(
    ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL,
    description=_(
        'Email sent to the candidate to inform him that he must pay the application fee to finalize '
        'an application for general education'
    ),
    tag=GENERAL_ADMISSION_TAG,
    tokens=CHECKLIST_TOKENS
    + [
        Token(
            name='admissions_link_front',
            description=_("Link to the admissions (front-office)"),
            example="http://dev.studies.uclouvain.be/somewhere",
        ),
    ],
)


ADMISSION_EMAIL_SEND_TO_FAC_AT_FAC_DECISION_GENERAL = 'osis-admission-send-to-fac-at-fac-decision-general'
templates.register(
    ADMISSION_EMAIL_SEND_TO_FAC_AT_FAC_DECISION_GENERAL,
    description=_(
        'Email sent to the faculty when the SIC submits the application during the faculty decision process.',
    ),
    tag=GENERAL_ADMISSION_TAG,
    tokens=CHECKLIST_TOKENS
    + [
        Token(
            name='admission_link_back_for_fac_approval_checklist',
            description=_("Link to the page of the faculty decision in the checklist of the admission (back-office)"),
            example="http://dev.studies.uclouvain.be/somewhere",
        ),
        Token(
            name='admission_link_back_for_uclouvain_documents',
            description=_("Link to the page of the documents of the admission (back-office)"),
            example="http://dev.studies.uclouvain.be/somewhere",
        ),
        Token(
            name='candidate_nationality_country',
            description=_("Candidate's country of nationality"),
            example="Belgique",
        ),
    ],
)
