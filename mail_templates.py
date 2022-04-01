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

common_tokens = [
    Token(
        name='candidate_first_name',
        description=_("The first name of the candidate"),
        example="John",
    ),
    Token(
        name='candidate_last_name',
        description=_("The last name of the candidate"),
        example="Doe",
    ),
    Token(
        name='doctorate_title',
        description=_("Title of the doctorate"),
        example="Doctorat en sciences de la santé publique",
    ),
    Token(
        name='admission_link_front',
        description=_("Link to the admission (front-office)"),
        example="http://dev.studies.uclouvain.be/somewhere",
    ),
    Token(
        name='admission_link_back',
        description=_("Link to the admission (back-office)"),
        example="http://dev.osis.uclouvain.be/somewhere",
    ),
]

ADMISSION_EMAIL_SIGNATURE_REQUESTS_CANDIDATE = 'osis-admission-signature-requests-candidate'
templates.register(
    ADMISSION_EMAIL_SIGNATURE_REQUESTS_CANDIDATE,
    description=_("Mail sent to the candidate to confirm supervision group signature requests are sent"),
    tokens=common_tokens
    + [
        Token(
            name='actors_as_list_items',
            description=_("Actors as list items"),
            example="Jean</li><li>Eudes",
        ),
        Token(
            name='actors_comma_separated',
            description=_("Actors, comma-separated"),
            example="Jean, Eudes",
        ),
    ],
    tag='Admission',
)

signataire_tokens = [
    Token(
        name='signataire_first_name',
        description=_("The first name of the signing actor"),
        example="Jim",
    ),
    Token(
        name='signataire_last_name',
        description=_("The last name of the signing actor"),
        example="Halpert",
    ),
    Token(
        name='signataire_role',
        description=_("Role of the signing actor"),
        example="promoteur",
    ),
]

ADMISSION_EMAIL_SIGNATURE_REQUESTS_ACTOR = 'osis-admission-signature-requests-actor'
templates.register(
    ADMISSION_EMAIL_SIGNATURE_REQUESTS_ACTOR,
    description=_("Mail sent to each actor of the supervision group to request a signature"),
    tokens=common_tokens + signataire_tokens,
    tag='Admission',
)

ADMISSION_EMAIL_SIGNATURE_CANDIDATE = 'osis-admission-signature-candidate'
templates.register(
    ADMISSION_EMAIL_SIGNATURE_CANDIDATE,
    description=_("Mail sent to the candidate after each signature"),
    tokens=common_tokens
    + signataire_tokens
    + [
        Token(
            name='decision',
            description=_("The decision of the signing actor"),
            example="Approved",
        ),
        Token(
            name='comment',
            description=_("The public comment about the approval/refusal"),
            example="I would be glad to supervise you",
        ),
        Token(
            name='reason',
            description=_("The reason for refusal"),
            example="I do not handle this kind of doctorates",
        ),
    ],
    tag='Admission',
)

ADMISSION_EMAIL_SIGNATURE_REFUSAL = 'osis-admission-signature-refusal'
templates.register(
    ADMISSION_EMAIL_SIGNATURE_REFUSAL,
    description=_("Mail sent to other promoter after a refusal"),
    tokens=common_tokens
    + signataire_tokens
    + [
        Token(
            name='decision',
            description=_("The decision of the signing actor"),
            example="Approved",
        ),
        Token(
            name='comment',
            description=_("The public comment about the approval/refusal"),
            example="I would be glad to supervise you",
        ),
        Token(
            name='reason',
            description=_("The reason for refusal"),
            example="I do not handle this kind of doctorates",
        ),
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
    tag='Admission',
)


ADMISSION_EMAIL_SUBMISSION_CANDIDATE = 'osis-admission-submission-candidate'
templates.register(
    ADMISSION_EMAIL_SUBMISSION_CANDIDATE,
    description=_("Mail sent to the candidate to confirm submission"),
    tokens=common_tokens,
    tag='Admission',
)

ADMISSION_EMAIL_SUBMISSION_CDD = 'osis-admission-submission-cdd'
templates.register(
    ADMISSION_EMAIL_SUBMISSION_CDD,
    description=_("Mail sent to the CDD to confirm submission"),
    tokens=common_tokens
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
    tag='Admission',
)

ADMISSION_EMAIL_SUBMISSION_MEMBER = 'osis-admission-submission-member'
templates.register(
    ADMISSION_EMAIL_SUBMISSION_MEMBER,
    description=_("Mail sent to a supervision member to confirm submission"),
    tokens=common_tokens
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
    tag='Admission',
)

ADMISSION_EMAIL_MEMBER_REMOVED = 'osis-admission-member-removed'
templates.register(
    ADMISSION_EMAIL_MEMBER_REMOVED,
    description=_("Mail sent to a supervision member when removed"),
    tokens=common_tokens
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
    tag='Admission',
)
