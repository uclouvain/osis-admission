# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

from functools import partial

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import get_language
from rest_framework import serializers

from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import INSTITUTE


class TranslatedField(serializers.SerializerMethodField):
    def __init__(self, field_name, en_field_name, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True

        super().__init__(**kwargs)

        self.field_name = field_name
        self.en_field_name = en_field_name

    def to_representation(self, value):
        if get_language() == settings.LANGUAGE_CODE_EN:
            return getattr(value, self.en_field_name)
        else:
            return getattr(value, self.field_name)


class RelatedInstituteField(serializers.CharField, serializers.SlugRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault('slug_field', 'uuid')
        kwargs.setdefault('queryset', EntityVersion.objects.filter(entity_type=INSTITUTE))
        kwargs.setdefault('allow_null', True)
        kwargs.setdefault('allow_blank', True)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if data:
            return serializers.SlugRelatedField.to_internal_value(self, data)

    def to_representation(self, value):
        if value:
            return str(serializers.SlugRelatedField.to_representation(self, value))


AdmissionUuidField = partial(
    serializers.SlugRelatedField,
    slug_field='uuid',
    read_only=True,
    allow_null=True,
)


AnswerToSpecificQuestionField = partial(
    serializers.JSONField,
    encoder=DjangoJSONEncoder,
    default=dict,
)


# Available actions
ACTION_LINKS = {
    # List
    # Normal
    'list_propositions': {
        'path_name': 'admission_api_v1:propositions',
        'method': 'GET',
    },
    'create_training_choice': {
        'path_name': 'admission_api_v1:propositions',
        'method': 'POST',
    },
    # Create
    'update_person': {
        'path_name': 'admission_api_v1:person',
        'method': 'PUT',
    },
    'update_coordinates': {
        'path_name': 'admission_api_v1:coordonnees',
        'method': 'PUT',
    },
    # Supervised
    'list_supervised': {
        'path_name': 'admission_api_v1:supervised_propositions',
        'method': 'GET',
    },
}

DOCTORATE_ACTION_LINKS = {
    # Person
    'retrieve_person': {
        'path_name': 'admission_api_v1:person',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_person': {
        'path_name': 'admission_api_v1:person',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Coordinates
    'retrieve_coordinates': {
        'path_name': 'admission_api_v1:coordonnees',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_coordinates': {
        'path_name': 'admission_api_v1:coordonnees',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Secondary studies
    'retrieve_secondary_studies': {
        'path_name': 'admission_api_v1:secondary-studies',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_secondary_studies': {
        'path_name': 'admission_api_v1:secondary-studies',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Languages knowledge
    'retrieve_languages': {
        'path_name': 'admission_api_v1:languages-knowledge',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_languages': {
        'path_name': 'admission_api_v1:languages-knowledge',
        'method': 'POST',
        'params': ['uuid'],
    },
    # Curriculum
    'retrieve_curriculum': {
        'path_name': 'admission_api_v1:doctorate_curriculum',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_curriculum': {
        'path_name': 'admission_api_v1:doctorate_curriculum',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Proposition
    # Project
    'create_doctorate_proposition': {
        'path_name': 'admission_api_v1:propositions',
        'method': 'POST',
    },
    'update_doctorate_training_choice': {
        'path_name': 'admission_api_v1:doctorate_admission_type_update',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_doctorate_training_choice': {
        'path_name': 'admission_api_v1:doctorate_admission_type_update',
        'method': 'GET',
        'params': ['uuid'],
    },
    'destroy_proposition': {
        'path_name': 'admission_api_v1:doctorate_propositions',
        'method': 'DELETE',
        'params': ['uuid'],
    },
    'retrieve_project': {
        'path_name': 'admission_api_v1:project',
        'method': 'GET',
        'params': ['uuid'],
    },
    'submit_proposition': {
        'path_name': 'admission_api_v1:submit-doctoral-proposition',
        'method': 'POST',
        'params': ['uuid'],
    },
    'update_project': {
        'path_name': 'admission_api_v1:project',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Cotutelle
    'retrieve_cotutelle': {
        'path_name': 'admission_api_v1:cotutelle',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_cotutelle': {
        'path_name': 'admission_api_v1:cotutelle',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Supervision
    'add_member': {
        'path_name': 'admission_api_v1:supervision',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'set_reference_promoter': {
        'path_name': 'admission_api_v1:set-reference-promoter',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'remove_member': {
        'path_name': 'admission_api_v1:supervision',
        'method': 'POST',
        'params': ['uuid'],
    },
    'edit_external_member': {
        'path_name': 'admission_api_v1:supervision',
        'method': 'PATCH',
        'params': ['uuid'],
    },
    'retrieve_supervision': {
        'path_name': 'admission_api_v1:supervision',
        'method': 'GET',
        'params': ['uuid'],
    },
    'add_approval': {
        'path_name': 'admission_api_v1:approvals',
        'method': 'POST',
        'params': ['uuid'],
    },
    'request_signatures': {
        'path_name': 'admission_api_v1:request-signatures',
        'method': 'POST',
        'params': ['uuid'],
    },
    'approve_by_pdf': {
        'path_name': 'admission_api_v1:approve-by-pdf',
        'method': 'POST',
        'params': ['uuid'],
    },
    # Confirmation exam
    'retrieve_confirmation': {
        'path_name': 'admission_api_v1:confirmation',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_confirmation': {
        'path_name': 'admission_api_v1:last_confirmation',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'update_confirmation_extension': {
        'path_name': 'admission_api_v1:last_confirmation',
        'method': 'POST',
        'params': ['uuid'],
    },
    # Training
    'add_training': {
        'path_name': 'admission_api_v1:doctoral-training',
        'method': 'POST',
        'params': ['uuid'],
    },
    'assent_training': {
        'path_name': 'admission_api_v1:training-assent',
        'method': 'POST',
        'params': ['uuid'],
    },
    'submit_training': {
        'path_name': 'admission_api_v1:training-submit',
        'method': 'POST',
        'params': ['uuid'],
    },
    'retrieve_doctoral_training': {
        'path_name': 'admission_api_v1:doctoral-training',
        'method': 'GET',
        'params': ['uuid'],
    },
    'retrieve_complementary_training': {
        'path_name': 'admission_api_v1:complementary-training',
        'method': 'GET',
        'params': ['uuid'],
    },
    'retrieve_course_enrollment': {
        'path_name': 'admission_api_v1:course-enrollment',
        'method': 'GET',
        'params': ['uuid'],
    },
    # Jury
    'retrieve_jury_preparation': {
        'path_name': 'admission_api_v1:jury-preparation',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_jury_preparation': {
        'path_name': 'admission_api_v1:jury-preparation',
        'method': 'POST',
        'params': ['uuid'],
    },
    'list_jury_members': {
        'path_name': 'admission_api_v1:jury-members-list',
        'method': 'GET',
        'params': ['uuid'],
    },
    'create_jury_members': {
        'path_name': 'admission_api_v1:jury-members-list',
        'method': 'POST',
        'params': ['uuid'],
    },
    # Accounting
    'retrieve_accounting': {
        'path_name': 'admission_api_v1:doctorate_accounting',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_accounting': {
        'path_name': 'admission_api_v1:doctorate_accounting',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Documents
    'retrieve_documents': {
        'path_name': 'admission_api_v1:doctorate_documents',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_documents': {
        'path_name': 'admission_api_v1:doctorate_documents',
        'method': 'POST',
        'params': ['uuid'],
    },
}

GENERAL_EDUCATION_ACTION_LINKS = {
    'update_training_choice': {
        'path_name': 'admission_api_v1:general_training_choice',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_training_choice': {
        'path_name': 'admission_api_v1:general_training_choice',
        'method': 'GET',
        'params': ['uuid'],
    },
    'destroy_proposition': {
        'path_name': 'admission_api_v1:general_propositions',
        'method': 'DELETE',
        'params': ['uuid'],
    },
    'submit_proposition': {
        'path_name': 'admission_api_v1:submit-general-proposition',
        'method': 'POST',
        'params': ['uuid'],
    },
    'retrieve_person': {
        'path_name': 'admission_api_v1:general_person',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_person': {
        'path_name': 'admission_api_v1:general_person',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_coordinates': {
        'path_name': 'admission_api_v1:general_coordinates',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_coordinates': {
        'path_name': 'admission_api_v1:general_coordinates',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_secondary_studies': {
        'path_name': 'admission_api_v1:general_secondary_studies',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_secondary_studies': {
        'path_name': 'admission_api_v1:general_secondary_studies',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_curriculum': {
        'path_name': 'admission_api_v1:general_curriculum',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_curriculum': {
        'path_name': 'admission_api_v1:general_curriculum',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_specific_question': {
        'path_name': 'admission_api_v1:general_specific_question',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_specific_question': {
        'path_name': 'admission_api_v1:general_specific_question',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Accounting
    'retrieve_accounting': {
        'path_name': 'admission_api_v1:general_accounting',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_accounting': {
        'path_name': 'admission_api_v1:general_accounting',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Documents
    'retrieve_documents': {
        'path_name': 'admission_api_v1:general_documents',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_documents': {
        'path_name': 'admission_api_v1:general_documents',
        'method': 'POST',
        'params': ['uuid'],
    },
    # Payment
    'pay_after_submission': {
        'path_name': 'admission_api_v1:open_application_fees_payment',
        'method': 'POST',
        'params': ['uuid'],
    },
    'pay_after_request': {
        'path_name': 'admission_api_v1:open_application_fees_payment',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'view_payment': {
        'path_name': 'admission_api_v1:view_application_fees',
        'method': 'GET',
        'params': ['uuid'],
    },
}

CONTINUING_EDUCATION_ACTION_LINKS = {
    # Continuing education
    'create_proposition': {
        'path_name': 'admission_api_v1:continuing_training_choice',
        'method': 'POST',
    },
    'update_training_choice': {
        'path_name': 'admission_api_v1:continuing_training_choice',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_training_choice': {
        'path_name': 'admission_api_v1:continuing_training_choice',
        'method': 'GET',
        'params': ['uuid'],
    },
    'destroy_proposition': {
        'path_name': 'admission_api_v1:continuing_propositions',
        'method': 'DELETE',
        'params': ['uuid'],
    },
    'submit_proposition': {
        'path_name': 'admission_api_v1:submit-continuing-proposition',
        'method': 'POST',
        'params': ['uuid'],
    },
    'retrieve_person': {
        'path_name': 'admission_api_v1:continuing_person',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_person': {
        'path_name': 'admission_api_v1:continuing_person',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_coordinates': {
        'path_name': 'admission_api_v1:continuing_coordinates',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_coordinates': {
        'path_name': 'admission_api_v1:continuing_coordinates',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_secondary_studies': {
        'path_name': 'admission_api_v1:continuing_secondary_studies',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_secondary_studies': {
        'path_name': 'admission_api_v1:continuing_secondary_studies',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_curriculum': {
        'path_name': 'admission_api_v1:continuing_curriculum',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_curriculum': {
        'path_name': 'admission_api_v1:continuing_curriculum',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_specific_question': {
        'path_name': 'admission_api_v1:continuing_specific_question',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_specific_question': {
        'path_name': 'admission_api_v1:continuing_specific_question',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Documents
    'retrieve_documents': {
        'path_name': 'admission_api_v1:continuing_documents',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_documents': {
        'path_name': 'admission_api_v1:continuing_documents',
        'method': 'POST',
        'params': ['uuid'],
    },
}
