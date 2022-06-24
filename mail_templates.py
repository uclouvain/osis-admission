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

DOCTORATE_ADMISSION_TAG = 'Admission Doctorat'

common_tokens = [
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

admission_common_tokens = common_tokens + [
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
]

ADMISSION_EMAIL_SIGNATURE_REQUESTS_CANDIDATE = 'osis-admission-signature-requests-candidate'
templates.register(
    ADMISSION_EMAIL_SIGNATURE_REQUESTS_CANDIDATE,
    description=_("Mail sent to the candidate to confirm supervision group signature requests are sent"),
    tokens=admission_common_tokens
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
    tag=DOCTORATE_ADMISSION_TAG,
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
    Token(
        name='admission_link_front_supervision',
        description=_("Link to the admission supervisory panel (front-office)"),
        example="http://dev.studies.uclouvain.be/somewhere/some-uuid/supervision",
    ),
]

ADMISSION_EMAIL_SIGNATURE_REQUESTS_ACTOR = 'osis-admission-signature-requests-actor'
templates.register(
    ADMISSION_EMAIL_SIGNATURE_REQUESTS_ACTOR,
    description=_("Mail sent to each actor of the supervision group to request a signature"),
    tokens=admission_common_tokens + signataire_tokens,
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_SIGNATURE_CANDIDATE = 'osis-admission-signature-candidate'
templates.register(
    ADMISSION_EMAIL_SIGNATURE_CANDIDATE,
    description=_("Mail sent to the applicant following approval or rejection by a member of the supervisory group"),
    tokens=admission_common_tokens
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
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_SIGNATURE_REFUSAL = 'osis-admission-signature-refusal'
templates.register(
    ADMISSION_EMAIL_SIGNATURE_REFUSAL,
    description=_("Mail sent to promoters when a member of the supervision panel refuses"),
    tokens=admission_common_tokens
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
    tag=DOCTORATE_ADMISSION_TAG,
)


ADMISSION_EMAIL_SUBMISSION_CANDIDATE = 'osis-admission-submission-candidate'
templates.register(
    ADMISSION_EMAIL_SUBMISSION_CANDIDATE,
    description=_(
        "Mail sent to the candidate to confirm that his application has been taken into account by UCLouvain"
    ),
    tokens=admission_common_tokens,
    tag=DOCTORATE_ADMISSION_TAG,
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

# Doctorate
doctorate_common_tokens = common_tokens + [
    Token(
        name='student_first_name',
        description=_("The first name of the student"),
        example="John",
    ),
    Token(
        name='student_last_name',
        description=_("The last name of the student"),
        example="Doe",
    ),
]

confirmation_paper_tokens = doctorate_common_tokens + [
    Token(
        name='confirmation_paper_link_front',
        description=_("Link to the admission confirmation paper panel (front-office)"),
        example="http://dev.studies.uclouvain.be/somewhere/some-uuid/confirmation",
    ),
    Token(
        name='confirmation_paper_link_back',
        description=_("Link to the admission confirmation paper panel (back-office)"),
        example="http://dev.osis.uclouvain.be/somewhere/some-uuid/confirmation",
    ),
    Token(
        name='confirmation_paper_deadline',
        description=_("Deadline of the confirmation paper (DD/MM/YYYY)"),
        example="31/04/2022",
    ),
    Token(
        name='confirmation_paper_date',
        description=_("Date of the confirmation paper (DD/MM/YYYY)"),
        example="01/04/2022",
    ),
    Token(
        name='scholarship_grant_acronym',
        description=_("The acronym of the scholarship grant"),
        example="ARC",
    ),
]

ADMISSION_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE = 'osis-admission-confirmation-submission-adre'
templates.register(
    ADMISSION_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE,
    description=_("Mail sent to ADRE on first submission of the confirmation paper by the doctoral student"),
    tokens=confirmation_paper_tokens,
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT = 'osis-admission-confirmation-info-student'
templates.register(
    ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
    description=_("Mail sent to the doctoral student to give him some information about the confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT = 'osis-admission-confirmation-on-success-student'
templates.register(
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT,
    description=_(
        "Mail sent to the doctoral student to inform him of the favourable opinion on the confirmation paper"
    ),
    tokens=confirmation_paper_tokens,
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE = 'osis-admission-confirmation-on-success-adre'
templates.register(
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE,
    description=_("Mail sent to ADRE to inform him of the favourable opinion on one confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI = 'osis-admission-confirmation-on-success-adri'
templates.register(
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI,
    description=_("Mail sent to ADRI to inform him of the favourable opinion on one confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT = 'osis-admission-confirmation-on-failure-student'
templates.register(
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
    description=_(
        "Mail sent to the doctoral student to inform him of the defavourable opinion on the confirmation paper"
    ),
    tokens=confirmation_paper_tokens,
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE = 'osis-admission-confirmation-on-failure-adre'
templates.register(
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE,
    description=_("Mail sent to ADRE to inform him of the defavourable opinion on one confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI = 'osis-admission-confirmation-on-failure-adri'
templates.register(
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI,
    description=_("Mail sent to ADRI to inform him of the defavourable opinion on one confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT = 'osis-admission-confirmation-on-retaking-student'
templates.register(
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
    description=_("Mail sent to the doctoral student to inform him of the necessity to retake the confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE = 'osis-admission-confirmation-on-retaking-adre'
templates.register(
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE,
    description=_("Mail sent to ADRE to inform him of the necessity to retake one confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=DOCTORATE_ADMISSION_TAG,
)

ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI = 'osis-admission-confirmation-on-retaking-adri'
templates.register(
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI,
    description=_("Mail sent to ADRI to inform him of the necessity to retake one confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=DOCTORATE_ADMISSION_TAG,
)

CONFIRMATION_PAPER_TEMPLATES_IDENTIFIERS = {
    ADMISSION_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI,
}
