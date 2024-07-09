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
from .tokens import CONTINUING_ADMISSION_TAG, DOCTORATE_ADMISSION_TAG, GENERAL_ADMISSION_TAG, admission_common_tokens

__all__ = [
    "ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED",
    "ADMISSION_EMAIL_MEMBER_REMOVED",
    "ADMISSION_EMAIL_CONFIRM_SUBMISSION_DOCTORATE",
    "ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL",
    "ADMISSION_EMAIL_CONFIRM_SUBMISSION_CONTINUING",
]

ADMISSION_EMAIL_CONFIRM_SUBMISSION_DOCTORATE = 'osis-admission-submission-candidate'
templates.register(
    ADMISSION_EMAIL_CONFIRM_SUBMISSION_DOCTORATE,
    description=_(
        "Mail sent to the candidate to confirm that his application has been taken into account by UCLouvain"
    ),
    tokens=admission_common_tokens
    + [
        Token(
            name='training_acronym',
            description=_('Acronym of the training'),
            example='SPRI2MS/DI',
        ),
        Token(
            name='admission_reference',
            description=_('Reference of the admission'),
            example='L-ESPO24-100.102',
        ),
        Token(
            name='recap_link',
            description=_("Link to download a copy of the file related to the admission (frontoffice)."),
            example="https://dev.studies.uclouvain.be/somewhere",
        ),
    ],
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL = 'osis-admission-confirm-submission-general'
templates.register(
    ADMISSION_EMAIL_CONFIRM_SUBMISSION_GENERAL,
    description=_(
        "Mail sent to the candidate to confirm that his application for general education has been taken "
        "into account by UCLouvain"
    ),
    tokens=admission_common_tokens
    + [
        Token(
            name='salutation',
            description=_('Mail salutation'),
            example='Chère',
        ),
        Token(
            name='payment_sentence',
            description=_('Sentence indicating the payment of the application fee (if applicable).'),
            example='Le payement des frais de dossier a bien été réceptionné.',
        ),
        Token(
            name='late_enrolment_sentence',
            description=_('Sentence indicating the late enrolment (if applicable).'),
            example="Nous attirons votre attention sur le fait que vous avez introduit une demande d'inscription "
            "tardive. Le jury d'admission se réserve le droit d'accepter ou de refuser cette demande en raison "
            "des impératifs pédagogiques.",
        ),
        Token(
            name='enrolment_sentence',
            description=_('Sentence indicating the start date of the enrollment processing (if applicable).'),
            example="Pour votre bonne information, les dossiers d’inscription pour l’année académique 2024-2025 seront "
            "traités à partir de juillet 2024.",
        ),
        Token(
            name='recap_link',
            description=_("Link to download a copy of the file related to the admission (frontoffice)."),
            example="https://dev.studies.uclouvain.be/somewhere",
        ),
        Token(
            name='admission_reference',
            description=_('Reference of the admission'),
            example='L-ESPO24-100.102',
        ),
        Token(
            name='training_acronym',
            description=_('Acronym of the training'),
            example='SPRI2MS/DI',
        ),
    ],
    tag=GENERAL_ADMISSION_TAG,
)

ADMISSION_EMAIL_CONFIRM_SUBMISSION_CONTINUING = 'osis-admission-confirm-submission-continuing'
templates.register(
    ADMISSION_EMAIL_CONFIRM_SUBMISSION_CONTINUING,
    description=_(
        "Mail sent to the candidate to confirm that his application for continuing education has been taken "
        "into account by UCLouvain"
    ),
    tokens=admission_common_tokens
    + [
        Token(
            name='salutation',
            description=_('Mail salutation'),
            example='Chère',
        ),
        Token(
            name='recap_link',
            description=_("Expirable link to the admission recap"),
            example="https://dev.studies.uclouvain.be/somewhere",
        ),
        Token(
            name='admission_reference',
            description=_('Reference of the admission'),
            example='L-ESPO24-100.102',
        ),
        Token(
            name='training_acronym',
            description=_('Acronym of the training'),
            example='SPRI2MS/DI',
        ),
        Token(
            name='program_managers_emails',
            description=_("List of emails of the program managers."),
            example='john.doe@example.com or jane.doe@example.com',
        ),
        Token(
            name='program_managers_names',
            description=_("List of names of the program managers."),
            example='John Doe, Jane Doe',
        ),
    ],
    tag=CONTINUING_ADMISSION_TAG,
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
