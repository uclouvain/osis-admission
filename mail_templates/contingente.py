# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
    'ADMISSION_EMAIL_CONTINGENTE_CONFIRMATION',
]


ADMISSION_EMAIL_CONTINGENTE_CONFIRMATION = 'osis-admission-contingente-soumission'
templates.register(
    ADMISSION_EMAIL_CONTINGENTE_CONFIRMATION,
    description=_('Mail sent to the candidate to confirm the submission of his training with quota.'),
    tag=GENERAL_ADMISSION_TAG,
    tokens=admission_common_tokens
    + [
        Token(
            name='ares_application_number',
            description=_("The ares application number of the admission"),
            example="UCLouvain/K-250001",
        ),
        Token(
            name='receipt_document_link',
            description=_("The link to the receipt"),
            example="https://...",
        ),
    ],
)


ADMISSION_EMAIL_CONTINGENTE_ACCEPTATION = 'osis-admission-contingente-acceptation'
templates.register(
    ADMISSION_EMAIL_CONTINGENTE_ACCEPTATION,
    description=_('Mail sent to the candidate to notify him of the acceptance of their admission.'),
    tag=GENERAL_ADMISSION_TAG,
    tokens=admission_common_tokens
    + [
        Token(
            name='ares_application_number',
            description=_("The ares application number of the admission"),
            example="UCLouvain/K-250001",
        ),
        Token(
            name='required_documents_paragraph',
            description=_('Paragraph including the required documents'),
            example=(
                'Par ailleurs, nous profitons de ce courrier pour vous signaler que les documents complémentaires '
                'ci-dessous sont à nous fournir dès que possible à l’adresse info-mons@uclouvain.be :'
            ),
        ),
        Token(
            name='acceptance_document_link',
            description=_("The link to the acceptance document"),
            example="https://...",
        ),
        Token(
            name='admission_link_front_requested_documents',
            description=_("Link to the request documents tab (front-office)"),
            example="http://dev.studies.uclouvain.be/somewhere",
        ),
        Token(
            name='academic_year',
            description=_("Academic year of the admission"),
            example="2023-2024",
        ),
        Token(
            name='deadline_date',
            description=_("The date before which the candidate must answer"),
            example="10/09/2026",
        ),
    ],
)
