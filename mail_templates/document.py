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
    'ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_GENERAL',
    'ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_GENERAL',
    'ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_DOCTORATE',
    'ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_DOCTORATE',
    'ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_CONTINUING',
    'ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_GENERAL',
    'ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_GENERAL',
    'ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_CONTINUING',
    'ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_CONTINUING',
    'ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_DOCTORATE',
    'ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_DOCTORATE',
]


DOCUMENT_TOKENS = admission_common_tokens + [
    Token(
        name='training_acronym',
        description=_('Acronym of the training'),
        example='ESP3DP',
    ),
    Token(
        name='training_campus',
        description=_('Teaching campus of the training'),
        example='Louvain-La-Neuve',
    ),
    Token(
        name='training_year',
        description=_('Year of the training'),
        example='2023-2024',
    ),
    Token(
        name='request_deadline',
        description=_('Deadline for the candidate to upload documents'),
        example='10th February 2023',
    ),
    Token(
        name='requested_documents',
        description=_('List of the mandatory requested documents that must be submitted immediately, with the reason'),
        example='Identity card. The format is unknown.',
    ),
    Token(
        name='later_requested_documents',
        description=_('List of the requested documents that can be submitted later, with the reason'),
        example='Identity card. The format is unknown.',
    ),
    Token(
        name='admission_reference',
        description=_('Reference of the admission'),
        example='L-ESPO24-100.102',
    ),
    Token(
        name='management_entity_name',
        description=_('Name of the management entity'),
        example='Faculté des sciences économiques, sociales, politiques et de communication',
    ),
    Token(
        name='management_entity_acronym',
        description=_('Acronym of the management entity'),
        example='ESPO',
    ),
    Token(
        name='admissions_link_front',
        description=_("Link to the admissions (front-office)"),
        example="http://dev.studies.uclouvain.be/somewhere",
    ),
    Token(
        name='salutation',
        description=_('Mail salutation'),
        example='Chère',
    ),
]

ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_GENERAL = 'osis-admission-request-sic-documents-general'
templates.register(
    ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_GENERAL,
    description=_(
        'Mail sent to the candidate to inform him that some SIC documents are missing or invalid '
        'in his application for general education'
    ),
    tag=GENERAL_ADMISSION_TAG,
    tokens=DOCUMENT_TOKENS,
)

ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_GENERAL = 'osis-admission-request-fac-documents-general'
templates.register(
    ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_GENERAL,
    description=_(
        'Mail sent to the candidate to inform him that some FAC documents are missing or invalid '
        'in his application for general education'
    ),
    tag=GENERAL_ADMISSION_TAG,
    tokens=DOCUMENT_TOKENS,
)

ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_DOCTORATE = 'osis-admission-request-sic-documents-doctorate'
templates.register(
    ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_DOCTORATE,
    description=_(
        'Mail sent to the candidate to inform him that some SIC documents are missing or invalid '
        'in his application for doctorate education'
    ),
    tag=DOCTORATE_ADMISSION_TAG,
    tokens=DOCUMENT_TOKENS,
)

ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_DOCTORATE = 'osis-admission-request-fac-documents-doctorate'
templates.register(
    ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_DOCTORATE,
    description=_(
        'Mail sent to the candidate to inform him that some FAC documents are missing or invalid '
        'in his application for doctorate education'
    ),
    tag=DOCTORATE_ADMISSION_TAG,
    tokens=DOCUMENT_TOKENS,
)


ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_CONTINUING = 'osis-admission-request-fac-documents-continuing'
templates.register(
    ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_CONTINUING,
    description=_(
        'Mail sent to the candidate to inform him that some FAC documents are missing or invalid '
        'in his application for continuing education'
    ),
    tag=CONTINUING_ADMISSION_TAG,
    tokens=DOCUMENT_TOKENS,
)


DOCUMENTS_CONFIRM_TOKENS = admission_common_tokens + [
    Token(
        name='training_acronym',
        description=_('Acronym of the training'),
        example='ESP3DP',
    ),
    Token(
        name='training_campus',
        description=_('Teaching campus of the training'),
        example='Louvain-La-Neuve',
    ),
    Token(
        name='training_year',
        description=_('Year of the training'),
        example='2023-2024',
    ),
    Token(
        name='requested_submitted_documents',
        description=_('List of the requested documents that have been submitted'),
        example=_('Identity card'),
    ),
    Token(
        name='requested_not_submitted_documents',
        description=_('List of the requested documents that haven\'t been submitted'),
        example=_('Identity card'),
    ),
    Token(
        name='admission_reference',
        description=_('Reference of the admission'),
        example='L-ESPO24-100.102',
    ),
    Token(
        name='salutation',
        description=_('Mail salutation'),
        example='Chère',
    ),
    Token(
        name='enrolment_service_email',
        description=_('Enrolment campus email'),
        example='inscription-lln@uclouvain.be',
    ),
]

ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_GENERAL = (
    'osis-admission-submission-confirm-with-submitted-and-not-submitted-general'
)
templates.register(
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_GENERAL,
    description=_(
        'Mail sent to the candidate to inform him that some requested documents have been received '
        'and some are still missing for general education'
    ),
    tag=GENERAL_ADMISSION_TAG,
    tokens=DOCUMENTS_CONFIRM_TOKENS,
)

ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_GENERAL = 'osis-admission-submission-confirm-with-submitted-general'
templates.register(
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_GENERAL,
    description=_(
        'Mail sent to the candidate to inform him that all requested documents have been received for general education'
    ),
    tag=GENERAL_ADMISSION_TAG,
    tokens=DOCUMENTS_CONFIRM_TOKENS,
)

ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_CONTINUING = (
    'osis-admission-submission-confirm-with-submitted-and-not-submitted-continuing'
)
templates.register(
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_CONTINUING,
    description=_(
        'Mail sent to the candidate to inform him that some requested documents have been received '
        'and some are still missing for continuing education'
    ),
    tag=CONTINUING_ADMISSION_TAG,
    tokens=DOCUMENTS_CONFIRM_TOKENS,
)

ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_CONTINUING = (
    'osis-admission-submission-confirm-with-submitted-continuing'
)
templates.register(
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_CONTINUING,
    description=_(
        'Mail sent to the candidate to inform him that all requested documents have been received for continuing '
        'education'
    ),
    tag=CONTINUING_ADMISSION_TAG,
    tokens=DOCUMENTS_CONFIRM_TOKENS,
)

ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_DOCTORATE = (
    'osis-admission-submission-confirm-with-submitted-and-not-submitted-doctorate'
)
templates.register(
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_DOCTORATE,
    description=_(
        'Mail sent to the candidate to inform him that some requested documents have been received '
        'and some are still missing for doctorate education'
    ),
    tag=DOCTORATE_ADMISSION_TAG,
    tokens=DOCUMENTS_CONFIRM_TOKENS,
)

ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_DOCTORATE = (
    'osis-admission-submission-confirm-with-submitted-doctorate'
)
templates.register(
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_DOCTORATE,
    description=_(
        'Mail sent to the candidate to inform him that all requested documents have been received '
        'for doctorate education'
    ),
    tag=DOCTORATE_ADMISSION_TAG,
    tokens=DOCUMENTS_CONFIRM_TOKENS,
)
