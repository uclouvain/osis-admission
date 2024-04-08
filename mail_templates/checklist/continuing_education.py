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

from admission.mail_templates.tokens import CONTINUING_ADMISSION_TAG, admission_common_tokens


CHECKLIST_TOKENS = admission_common_tokens + [
    Token(
        name='greetings',
        description=_("Greetings depending on the gender of the candidate"),
        example="Cher·ère",
    ),
    Token(
        name='application_reference',
        description=_('Reference of the application'),
        example='L-ESPO24-100.102',
    ),
    Token(
        name='training_acronym',
        description=_('Acronym of the training'),
        example='SPRI2MS/DI',
    ),
    Token(
        name='training_title',
        description=_('Title of the training'),
        example="Certificat d'université : Cybersécurité",
    ),
    Token(
        name='managers_emails',
        description=_('Emails of the training managers'),
        example="manager@example.org or other.manager@example.org",
    ),
    Token(
        name='application_link',
        description=_('Link to the application on the portal'),
        example="https://studies.uclouvain.be/...",
    ),
    Token(
        name='sender_name',
        description=_('Name of the manager sending the email'),
        example="John Doe",
    ),
]

ADMISSION_EMAIL_DECISION_FAC_APPROVAL_WITH_CONDITION = (
    'osis-admission-continuing-education-checklist-decision-fac-approval-with-condition'
)
templates.register(
    ADMISSION_EMAIL_DECISION_FAC_APPROVAL_WITH_CONDITION,
    description=_(
        'Email sent to the candidate when the faculty approve the application with condition.',
    ),
    tag=CONTINUING_ADMISSION_TAG,
    tokens=CHECKLIST_TOKENS
    + [
        Token(
            name='conditions',
            description=_("Condition for approval"),
            example="Condition for approval",
        ),
    ],
)

ADMISSION_EMAIL_DECISION_FAC_APPROVAL_WITHOUT_CONDITION = (
    'osis-admission-continuing-education-checklist-decision-fac-approval-without-condition'
)
templates.register(
    ADMISSION_EMAIL_DECISION_FAC_APPROVAL_WITHOUT_CONDITION,
    description=_(
        'Email sent to the candidate when the faculty approve the application with condition.',
    ),
    tag=CONTINUING_ADMISSION_TAG,
    tokens=CHECKLIST_TOKENS,
)

ADMISSION_EMAIL_DECISION_DENY = 'osis-admission-continuing-education-checklist-decision-deny'
templates.register(
    ADMISSION_EMAIL_DECISION_DENY,
    description=_(
        'Email sent to the candidate when IUFC or the faculty deny the application.',
    ),
    tag=CONTINUING_ADMISSION_TAG,
    tokens=CHECKLIST_TOKENS
    + [
        Token(
            name='reasons',
            description=_("Reasons for not accepting"),
            example="Reasons for not accepting",
        ),
    ],
)

ADMISSION_EMAIL_DECISION_ON_HOLD = 'osis-admission-continuing-education-checklist-decision-on-hold'
templates.register(
    ADMISSION_EMAIL_DECISION_ON_HOLD,
    description=_(
        'Email sent to the candidate when IUFC or the faculty put the application on hold.',
    ),
    tag=CONTINUING_ADMISSION_TAG,
    tokens=CHECKLIST_TOKENS
    + [
        Token(
            name='reasons',
            description=_("Reasons for putting on hold"),
            example="The programme is already full",
        ),
    ],
)

ADMISSION_EMAIL_DECISION_CANCEL = 'osis-admission-continuing-education-checklist-decision-cancel'
templates.register(
    ADMISSION_EMAIL_DECISION_CANCEL,
    description=_(
        'Email sent to the candidate when IUFC or the faculty cancel the application.',
    ),
    tag=CONTINUING_ADMISSION_TAG,
    tokens=CHECKLIST_TOKENS,
)

ADMISSION_EMAIL_DECISION_VALIDATION = 'osis-admission-continuing-education-checklist-decision-validation'
templates.register(
    ADMISSION_EMAIL_DECISION_VALIDATION,
    description=_(
        'Email sent to the candidate when IUFC validate the application.',
    ),
    tag=CONTINUING_ADMISSION_TAG,
    tokens=CHECKLIST_TOKENS,
)

ADMISSION_EMAIL_DECISION_IUFC_COMMENT_FOR_FAC = (
    'osis-admission-continuing-education-checklist-decision-iufc-comment-for-fac'
)
templates.register(
    ADMISSION_EMAIL_DECISION_IUFC_COMMENT_FOR_FAC,
    description=_(
        'Email sent to the faculty when IUFC needs more information.',
    ),
    tag=CONTINUING_ADMISSION_TAG,
    tokens=admission_common_tokens
    + [
        Token(
            name='application_reference',
            description=_('Reference of the application'),
            example='L-ESPO24-100.102',
        ),
        Token(
            name='training_acronym',
            description=_('Acronym of the training'),
            example='SPRI2MS/DI',
        ),
        Token(
            name='comment',
            description=_('Comment from IUFC to the faculty'),
            example="Comment from IUFC to the faculty",
        ),
        Token(
            name='application_link',
            description=_('Link to the application in the back-office'),
            example="https://osis.uclouvain.be/...",
        ),
        Token(
            name='sender_name',
            description=_('Name of the manager sending the email'),
            example="John Doe",
        ),
    ],
)
