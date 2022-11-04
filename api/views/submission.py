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

from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.settings import api_settings

from admission.api import serializers
from admission.api.schema import ResponseSpecificSchema
from admission.ddd.admission.doctorat.preparation.commands import (
    SoumettrePropositionCommand as SoumettrePropositionDoctoratCommand,
    VerifierProjetCommand,
    VerifierPropositionCommand as VerifierPropositionDoctoratCommand,
)
from admission.ddd.admission.doctorat.validation.commands import ApprouverDemandeCddCommand
from admission.ddd.admission.formation_continue.commands import (
    VerifierPropositionCommand as VerifierPropositionContinueCommand,
    SoumettrePropositionCommand as SoumettrePropositionContinueCommand,
)
from admission.ddd.admission.formation_generale.commands import (
    VerifierPropositionCommand as VerifierPropositionGeneraleCommand,
    SoumettrePropositionCommand as SoumettrePropositionGeneraleCommand,
)
from admission.utils import (
    gather_business_exceptions,
    get_cached_admission_perm_obj,
    get_cached_continuing_education_admission_perm_obj,
    get_cached_general_education_admission_perm_obj,
)
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    "VerifyDoctoralProjectView",
    "SubmitDoctoralPropositionView",
    "SubmitGeneralEducationPropositionView",
    "SubmitContinuingEducationPropositionView",
]


class VerifySchema(ResponseSpecificSchema):
    response_description = "Verification errors"

    def get_responses(self, path, method):
        return (
            {
                status.HTTP_200_OK: {
                    "description": self.response_description,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "status_code": {
                                            "type": "string",
                                        },
                                        "detail": {
                                            "type": "string",
                                        },
                                    },
                                },
                            }
                        }
                    },
                }
            }
            if method == 'GET'
            else super(VerifySchema, self).get_responses(path, method)
        )


class VerifyProjectSchema(VerifySchema):
    operation_id_base = '_verify_project'
    response_description = "Project verification errors"


class VerifyDoctoralProjectView(APIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "verify-project"
    schema = VerifyProjectSchema()
    permission_mapping = {
        'GET': 'admission.change_doctorateadmission_project',
    }
    pagination_class = None
    filter_backends = []

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Check the project to be OK with all validators."""
        data = gather_business_exceptions(VerifierProjetCommand(uuid_proposition=str(kwargs["uuid"])))
        return Response(data.get(api_settings.NON_FIELD_ERRORS_KEY, []), status=status.HTTP_200_OK)


class SubmitDoctoralPropositionSchema(VerifySchema):
    response_description = "Proposition verification errors"

    serializer_mapping = {
        'POST': serializers.PropositionIdentityDTOSerializer,
    }

    def get_operation_id(self, path, method):
        if method == 'GET':
            return 'verify_proposition'
        elif method == 'POST':
            return 'submit_proposition'
        return super().get_operation_id(path, method)


class SubmitDoctoralPropositionView(APIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "submit-doctoral-proposition"
    schema = SubmitDoctoralPropositionSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.submit_doctorateadmission',
        'POST': 'admission.submit_doctorateadmission',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Check the proposition to be OK with all validators."""
        data = gather_business_exceptions(VerifierPropositionDoctoratCommand(uuid_proposition=str(kwargs["uuid"])))
        return Response(data.get(api_settings.NON_FIELD_ERRORS_KEY, []), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Submit the proposition."""
        # Trigger the submit command
        proposition_id = message_bus_instance.invoke(
            SoumettrePropositionDoctoratCommand(uuid_proposition=str(kwargs["uuid"]))
        )
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        # TODO To remove when the admission approval by CDD and SIC will be created
        message_bus_instance.invoke(ApprouverDemandeCddCommand(uuid=str(kwargs["uuid"])))
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitGeneralEducationPropositionSchema(VerifySchema):
    response_description = "Proposition verification errors"
    serializer_mapping = {
        'POST': serializers.PropositionIdentityDTOSerializer,
    }

    def get_operation_id(self, path, method):
        return 'verify_general_education_proposition' if method == 'GET' else 'submit_general_education_proposition'


class SubmitGeneralEducationPropositionView(APIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "submit-general-proposition"
    schema = SubmitGeneralEducationPropositionSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.submit_generaleducationadmission',
        'POST': 'admission.submit_generaleducationadmission',
    }

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Check the proposition to be OK with all validators."""
        data = gather_business_exceptions(VerifierPropositionGeneraleCommand(uuid_proposition=str(kwargs["uuid"])))
        return Response(data.get(api_settings.NON_FIELD_ERRORS_KEY, []), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Submit the proposition."""
        proposition_id = message_bus_instance.invoke(
            SoumettrePropositionGeneraleCommand(uuid_proposition=str(kwargs["uuid"]))
        )
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitContinuingEducationPropositionSchema(VerifySchema):
    response_description = "Proposition verification errors"
    serializer_mapping = {
        'POST': serializers.PropositionIdentityDTOSerializer,
    }

    def get_operation_id(self, path, method):
        return (
            'verify_continuing_education_proposition' if method == 'GET' else 'submit_continuing_education_proposition'
        )


class SubmitContinuingEducationPropositionView(APIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "submit-continuing-proposition"
    schema = SubmitContinuingEducationPropositionSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.submit_continuingeducationadmission',
        'POST': 'admission.submit_continuingeducationadmission',
    }

    def get_permission_object(self):
        return get_cached_continuing_education_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Check the proposition to be OK with all validators."""
        data = gather_business_exceptions(VerifierPropositionContinueCommand(uuid_proposition=str(kwargs["uuid"])))
        return Response(data.get(api_settings.NON_FIELD_ERRORS_KEY, []), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Submit the proposition."""
        proposition_id = message_bus_instance.invoke(
            SoumettrePropositionContinueCommand(uuid_proposition=str(kwargs["uuid"]))
        )
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)
