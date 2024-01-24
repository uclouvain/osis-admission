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
            name='training_enrollment_campus_email',
            description=_("Email of the enrollment campus"),
            example="inscription-lln@uclouvain.be",
        ),
        Token(
            name='candidate_nationality_country',
            description=_("Candidate's country of nationality"),
            example="Belgique",
        ),
        Token(
            name='training_acronym',
            description=_('Acronym of the training'),
            example='SPRI2MS/DI',
        ),
    ],
)


ADMISSION_EMAIL_SIC_REFUSAL = 'osis-admission-sic-refusal'
templates.register(
    ADMISSION_EMAIL_SIC_REFUSAL,
    description=_(
        'Email sent to the candidate when SIC refuses an admission.',
    ),
    tag=GENERAL_ADMISSION_TAG,
    tokens=CHECKLIST_TOKENS
    + [
        Token(
            name='candidate',
            description=_("Candidate of the admission"),
            example="John Doe",
        ),
        Token(
            name='academic_year',
            description=_("Academic year of the admission"),
            example="2023-2024",
        ),
        Token(
            name='admission_training',
            description=_("Training of the admission"),
            example="AGRO3DP / Doctorat en sciences agronomiques et ingénierie biologique",
        ),
    ],
)


ADMISSION_EMAIL_SIC_APPROVAL = 'osis-admission-sic-approval'
templates.register(
    ADMISSION_EMAIL_SIC_APPROVAL,
    description=_(
        'Email sent to the candidate when SIC approves an admission.',
    ),
    tag=GENERAL_ADMISSION_TAG,
    tokens=CHECKLIST_TOKENS
    + [
        Token(
            name='candidate',
            description=_("Candidate of the admission"),
            example="John Doe",
        ),
        Token(
            name='academic_year',
            description=_("Academic year of the admission"),
            example="2023-2024",
        ),
        Token(
            name='academic_year_start_date',
            description=_("Start date of the academic year of the admission"),
            example="14 September",
        ),
        Token(
            name='admission_email',
            description=_("Email receiving the documents"),
            example="inscription-lln@uclouvain.be",
        ),
        Token(
            name='admission_training',
            description=_("Training of the admission"),
            example="Première année de bachelier en sciences informatiques (Louvain-la-Neuve) - SINF11BA",
        ),
        Token(
            name='greetings',
            description=_("Greetings depending on the gender of the candidate"),
            example="Cher·ère",
        ),
    ],
)
