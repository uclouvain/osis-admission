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

from admission.mail_templates.tokens import DOCTORATE_ADMISSION_TAG, admission_common_tokens


CHECKLIST_TOKENS = admission_common_tokens + [
    Token(
        name='admission_reference',
        description=_('Reference of the admission'),
        example='L-ESPO24-100.102',
    ),
]


ADMISSION_EMAIL_SEND_TO_FAC_AT_FAC_DECISION_DOCTORATE = 'osis-admission-send-to-fac-at-fac-decision-doctorate'
templates.register(
    ADMISSION_EMAIL_SEND_TO_FAC_AT_FAC_DECISION_DOCTORATE,
    description=_(
        'Email sent to the faculty when the SIC submits the application during the faculty decision process '
        'for a doctorate admission.',
    ),
    tag=DOCTORATE_ADMISSION_TAG,
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
        Token(
            name='application_type',
            description=_('Type of the application'),
            example='admission',
        ),
    ],
)


ADMISSION_EMAIL_SIC_REFUSAL_DOCTORATE = 'osis-admission-sic-refusal-doctorate'
templates.register(
    ADMISSION_EMAIL_SIC_REFUSAL_DOCTORATE,
    description=_(
        'Email sent to the candidate when SIC refuses a doctorate admission.',
    ),
    tag=DOCTORATE_ADMISSION_TAG,
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
        Token(
            name='document_link',
            description=_("Refusal document link"),
            example="https://osis.uclouvain.be/...",
        ),
    ],
)


EMAIL_TEMPLATE_ENROLLMENT_AUTHORIZATION_DOCUMENT_URL_DOCTORATE_TOKEN = 'LIEN_DOCUMENT_AUTORISATION_INSCRIPTION'
EMAIL_TEMPLATE_VISA_APPLICATION_DOCUMENT_URL_DOCTORATE_TOKEN = 'LIEN_DOCUMENT_DEMANDE_VISA'

ADMISSION_EMAIL_SIC_APPROVAL_DOCTORATE = 'osis-admission-sic-approval-doctorate'
ADMISSION_EMAIL_SIC_APPROVAL_TOKENS = CHECKLIST_TOKENS + [
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
        name='greetings',
        description=_("Greetings depending on the gender of the candidate"),
        example="Cher·ère",
    ),
    Token(
        name='enrollment_authorization_document_link',
        description=_("Enrollment authorization document link"),
        example="https://osis.uclouvain.be/...",
    ),
    Token(
        name='visa_application_document_link',
        description=_("Visa application document link"),
        example="https://osis.uclouvain.be/...",
    ),
    Token(
        name='training_campus',
        description=_('Teaching campus of the training'),
        example="Louvain-la-Neuve",
    ),
    Token(
        name='training_acronym',
        description=_('Acronym of the training'),
        example='SPRI2MS/DI',
    ),
]
templates.register(
    ADMISSION_EMAIL_SIC_APPROVAL_DOCTORATE,
    description=_(
        'Email sent to the NEU+5 candidate when SIC approves a doctorate admission.',
    ),
    tag=DOCTORATE_ADMISSION_TAG,
    tokens=ADMISSION_EMAIL_SIC_APPROVAL_TOKENS,
)
ADMISSION_EMAIL_SIC_APPROVAL_EU_DOCTORATE = 'osis-admission-sic-approval-eu-doctorate'
templates.register(
    ADMISSION_EMAIL_SIC_APPROVAL_EU_DOCTORATE,
    description=_(
        'Email sent to the EU+5 candidate when SIC approves a doctorate admission.',
    ),
    tag=DOCTORATE_ADMISSION_TAG,
    tokens=ADMISSION_EMAIL_SIC_APPROVAL_TOKENS,
)


EMAIL_TEMPLATE_ENROLLMENT_GENERATED_NOMA_DOCTORATE_TOKEN = 'NOMA_GENERE_NOUVEL_ETUDIANT'

INSCRIPTION_EMAIL_SIC_APPROVAL_DOCTORATE = 'osis-inscription-sic-approval-doctorate'
INSCRIPTION_EMAIL_SIC_APPROVAL_TOKENS = CHECKLIST_TOKENS + [
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
        name='greetings',
        description=_("Greetings depending on the gender of the candidate"),
        example="Cher·ère",
    ),
    Token(
        name='enrollment_authorization_document_link',
        description=_("Enrollment authorization document link"),
        example="https://osis.uclouvain.be/...",
    ),
    Token(
        name='visa_application_document_link',
        description=_("Visa application document link"),
        example="https://osis.uclouvain.be/...",
    ),
    Token(
        name='training_campus',
        description=_('Teaching campus of the training'),
        example="Louvain-la-Neuve",
    ),
    Token(
        name='training_acronym',
        description=_('Acronym of the training'),
        example='SPRI2MS/DI',
    ),
    Token(
        name='noma',
        description=_('Noma of the candidate'),
        example='',
    ),
    Token(
        name='contact_person_paragraph',
        description=_('Paragraph including the person to contact'),
        example='Personne de contact pour la composition du programme annuel : John Dow.',
    ),
    Token(
        name='planned_years_paragraph',
        description=_('Paragraph including the planned years'),
        example='Durée des études : 2 ans.',
    ),
    Token(
        name='prerequisite_courses_paragraph',
        description=_('Paragraph including the prerequisite courses'),
        example=(
            'Au vu de votre parcours antérieur, votre faculté complétera votre programme annuel par des '
            'compléments de formation (enseignements supplémentaires) (pour plus d’informations :'
            ' https://uclouvain.be/prog-2024-gest2m1-cond_adm). »'
        ),
    ),
    Token(
        name='prerequisite_courses_detail_paragraph',
        description=_('Paragraph including the prerequisite courses detail'),
        example='Détail des compléments de formation :',
    ),
    Token(
        name='required_documents_paragraph',
        description=_('Paragraph including the required documents'),
        example=(
            'Par ailleurs, nous profitons de ce courrier pour vous signaler que les documents complémentaires '
            'ci-dessous sont à nous fournir dès que possible à l’adresse info-mons@uclouvain.be :'
        ),
    ),
]
templates.register(
    INSCRIPTION_EMAIL_SIC_APPROVAL_DOCTORATE,
    description=_(
        'Email sent to the candidate when SIC approves a doctorate inscription.',
    ),
    tag=DOCTORATE_ADMISSION_TAG,
    tokens=INSCRIPTION_EMAIL_SIC_APPROVAL_TOKENS,
)

ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CHECKERS_DOCTORATE = (
    'osis-admission-check-background-authentication-to-checkers-doctorate'
)
templates.register(
    ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CHECKERS_DOCTORATE,
    description=_(
        'Email sent to the checkers to inform them to check the background authentication of the candidate for '
        'a doctorate admission.'
    ),
    tag=DOCTORATE_ADMISSION_TAG,
    tokens=CHECKLIST_TOKENS
    + [
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

ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CANDIDATE_DOCTORATE = (
    'osis-admission-check-background-authentication-to-candidate-doctorate'
)
templates.register(
    ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CANDIDATE_DOCTORATE,
    description=_(
        'Email sent to the candidate to inform him that the checking of the authentication of its background '
        'is in progress for a doctorate admission.'
    ),
    tag=DOCTORATE_ADMISSION_TAG,
    tokens=CHECKLIST_TOKENS
    + [
        Token(
            name='training_acronym',
            description=_('Acronym of the training'),
            example='SPRI2MS/DI',
        ),
        Token(
            name='training_campus',
            description=_('Teaching campus of the training'),
            example="Louvain-la-Neuve",
        ),
    ],
)

ADMISSION_EMAIL_FINANCABILITY_DISPENSATION_NOTIFICATION_DOCTORATE = (
    'osis-admission-financability-dispensation-notification-doctorate'
)
templates.register(
    ADMISSION_EMAIL_FINANCABILITY_DISPENSATION_NOTIFICATION_DOCTORATE,
    description=_(
        'Email sent to the candidate to inform him that a financability dispensation is needed for a '
        'doctorate admission.'
    ),
    tag=DOCTORATE_ADMISSION_TAG,
    tokens=CHECKLIST_TOKENS
    + [
        Token(
            name='training_acronym',
            description=_('Acronym of the training'),
            example='SPRI2MS/DI',
        ),
        Token(
            name='training_campus',
            description=_('Teaching campus of the training'),
            example="Louvain-la-Neuve",
        ),
        Token(
            name='academic_year',
            description=_("Academic year of the admission"),
            example="2023-2024",
        ),
        Token(
            name='greetings',
            description=_("Greetings depending on the gender of the candidate"),
            example="Cher",
        ),
        Token(
            name='greetings_end',
            description=_("Greetings depending on the gender of the candidate"),
            example="Madame",
        ),
        Token(
            name='contact_link',
            description=_("Contact link"),
            example="https://osis.uclouvain.be/...",
        ),
    ],
)
