# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from functools import partial

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder
from django.urls.exceptions import NoReverseMatch
from django.urls import reverse, resolve
from django.utils.translation import get_language

from rest_framework import serializers

from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import INSTITUTE
from osis_role.contrib.views import APIPermissionRequiredMixin


class TranslatedField(serializers.SerializerMethodField):
    def __init__(self, field_name, en_field_name, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True

        super().__init__(**kwargs)

        self.field_name = field_name
        self.en_field_name = en_field_name

    def to_representation(self, value):
        if get_language() == settings.LANGUAGE_CODE:
            return getattr(value, self.field_name)
        else:
            return getattr(value, self.en_field_name)


class ActionLinksField(serializers.Field):
    """
    Returns a dictionary of actions and their related endpoint (url + method type) that depend on user permissions.
    """

    def __init__(self, actions, **kwargs):
        kwargs.setdefault('default', {})
        kwargs.setdefault('source', '*')
        kwargs.setdefault('read_only', True)
        self.actions = actions
        super().__init__(**kwargs)

    def to_representation(self, instance):
        links = {}

        # Get the mandatory parameters from the context
        try:
            request = self.context['request']
        except KeyError:
            raise ImproperlyConfigured(
                "The 'request' property must be added to the serializer context to compute the action links."
            )

        # Get a dictionary of the available actions with their related endpoint (URL & HTTP method)
        for action_name, action in self.actions.items():

            # Get the url params
            if isinstance(action.get('params'), list):
                try:
                    url_args = [getattr(instance, param_name) for param_name in action['params']]
                except AttributeError as error:
                    raise ImproperlyConfigured(error)
            else:
                url_args = []

            # Build the view url
            try:
                url = reverse(action.get('path_name'), args=url_args)
            except NoReverseMatch:
                raise ImproperlyConfigured(
                    "Please check the following path exists: '{}'".format(action.get('path_name'))
                )

            # Find the view related to this url
            resolver_match = resolve(url)
            view_class = resolver_match.func.view_class

            if issubclass(view_class, APIPermissionRequiredMixin):
                view = view_class(args=resolver_match.args, kwargs=resolver_match.kwargs)

                # Check the permissions specified in the view via the 'permission_mapping' property
                failed_permission_message = view.check_method_permissions(
                    user=request.user,
                    method=action.get('method'),
                    obj=getattr(instance, '_perm_obj', None),
                )

                if failed_permission_message is None:
                    # If the user has the rights permissions we return the method type and the related endpoint
                    links[action_name] = {
                        'method': action.get('method'),
                        'url': url,
                    }
                else:
                    # Return the error message as the user hasn't got the right permissions
                    links[action_name] = {
                        'error': failed_permission_message,
                    }

            else:
                raise ImproperlyConfigured(
                    "All paths specified in the 'links' property must be related to views that implement "
                    "the '{}' mixin".format(APIPermissionRequiredMixin.__name__)
                )

        return links


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
        'path_name': 'admission_api_v1:propositions',
        'method': 'DELETE',
        'params': ['uuid'],
    },
    'retrieve_proposition': {
        'path_name': 'admission_api_v1:propositions',
        'method': 'GET',
        'params': ['uuid'],
    },
    'submit_proposition': {
        'path_name': 'admission_api_v1:submit-doctoral-proposition',
        'method': 'POST',
        'params': ['uuid'],
    },
    'update_proposition': {
        'path_name': 'admission_api_v1:propositions',
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
    # Confirmation paper
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
}

GENERAL_EDUCATION_ACTION_LINKS = {
    'update_training_choice': {
        'path_name': 'admission_api_v1:general_training_choice',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_training_choice': {
        'path_name': 'admission_api_v1:general_propositions',
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
        'path_name': 'admission_api_v1:continuing_propositions',
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
}
