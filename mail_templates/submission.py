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
from django.utils.translation import gettext_lazy as _

from osis_mail_template import Token, templates
from .tokens import CONTINUING_ADMISSION_TAG, DOCTORATE_ADMISSION_TAG, GENERAL_ADMISSION_TAG, admission_common_tokens

__all__ = [
    "ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED",
    "ADMISSION_EMAIL_MEMBER_REMOVED",
    "ADMISSION_EMAIL_CONFIRM_SUBMISSION_DOCTORATE",
    "ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL",
    "ADMISSION_EMAIL_CONFIRM_SUBMISSION_CONTINUING",
    "ADMISSION_EMAIL_SUBMISSION_CDD",
    "ADMISSION_EMAIL_SUBMISSION_MEMBER",
]

ADMISSION_EMAIL_CONFIRM_SUBMISSION_DOCTORATE = 'osis-admission-submission-candidate'
templates.register(
    ADMISSION_EMAIL_CONFIRM_SUBMISSION_DOCTORATE,
    description=_(
        "Mail sent to the candidate to confirm that his application has been taken into account by UCLouvain"
    ),
    tokens=admission_common_tokens,
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL = 'osis-admission-confirm-submission-general'
templates.register(
    ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL,
    description=_(
        "Mail sent to the candidate to confirm that his application for general education has been taken "
        "into account by UCLouvain"
    ),
    tokens=admission_common_tokens,
    tag=GENERAL_ADMISSION_TAG,
)

ADMISSION_EMAIL_CONFIRM_SUBMISSION_CONTINUING = 'osis-admission-confirm-submission-continuing'
templates.register(
    ADMISSION_EMAIL_CONFIRM_SUBMISSION_CONTINUING,
    description=_(
        "Mail sent to the candidate to confirm that his application for continuing education has been taken "
        "into account by UCLouvain"
    ),
    tokens=admission_common_tokens,
    tag=CONTINUING_ADMISSION_TAG,
)

ADMISSION_EMAIL_SUBMISSION_CDD = 'osis-admission-submission-cdd'
templates.register(
    ADMISSION_EMAIL_SUBMISSION_CDD,
    description=_("Mail sent to the CDD to inform them that a new application has been submitted"),
    tokens=admission_common_tokens
    + [
        Token(
            name='actor_first_name',
            description=_("The first name of the recipient"),
            example="Jane",
        ),
        Token(
            name='actor_last_name',
            description=_("The last name of the recipient"),
            example="Smith",
        ),
    ],
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_SUBMISSION_MEMBER = 'osis-admission-submission-member'
templates.register(
    ADMISSION_EMAIL_SUBMISSION_MEMBER,
    description=_(
        "Mail sent to the members of the supervision panel to inform them "
        "that the application has been submitted to UCLouvain by the applicant"
    ),
    tokens=admission_common_tokens
    + [
        Token(
            name='actor_first_name',
            description=_("The first name of the recipient"),
            example="Jane",
        ),
        Token(
            name='actor_last_name',
            description=_("The last name of the recipient"),
            example="Smith",
        ),
    ],
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_MEMBER_REMOVED = 'osis-admission-member-removed'
templates.register(
    ADMISSION_EMAIL_MEMBER_REMOVED,
    description=_("Mail sent to the member of the supervision panel when deleted by the candidate"),
    tokens=admission_common_tokens
    + [
        Token(
            name='actor_first_name',
            description=_("The first name of the recipient"),
            example="Jane",
        ),
        Token(
            name='actor_last_name',
            description=_("The last name of the recipient"),
            example="Smith",
        ),
    ],
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED = 'osis-admission-generic-admitted'
templates.register(
    ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED,
    description=_("Generic mail that can be manually sent once the candidate is admitted"),
    tokens=admission_common_tokens,
)
