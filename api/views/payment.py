# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admission.api import serializers
from admission.api.schema import ResponseSpecificSchema
from admission.ddd.admission.formation_generale.commands import (
    PayerFraisDossierPropositionSuiteDemandeCommand,
    PayerFraisDossierPropositionSuiteSoumissionCommand,
)
from admission.utils import get_cached_general_education_admission_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    'PayApplicationFeesAfterSubmissionView',
    'PayApplicationFeesAfterRequestView',
]


class PayApplicationFeesAfterSubmissionSchema(ResponseSpecificSchema):
    operation_id_base = '_application_fees_after_submission'
    serializer_mapping = {
        'POST': (
            serializers.PayerFraisDossierPropositionSuiteSoumissionCommandSerializer,
            serializers.PropositionIdentityDTOSerializer,
        ),
    }

    def get_operation_id(self, path, method):
        return 'pay_application_fees_after_submission'


class PayApplicationFeesAfterSubmissionView(
    APIPermissionRequiredMixin,
    APIView,
):
    name = "pay_after_submission"
    schema = PayApplicationFeesAfterSubmissionSchema()
    permission_mapping = {
        'POST': 'admission.pay_generaleducationadmission_fees',
    }

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])

    def post(self, request, *args, **kwargs):
        """Pay the application fee of the proposition after its submission."""
        proposition_id = message_bus_instance.invoke(
            PayerFraisDossierPropositionSuiteSoumissionCommand(uuid_proposition=str(self.kwargs['uuid']))
        )
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PayApplicationFeesAfterRequestSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'POST': (
            serializers.PayerFraisDossierPropositionSuiteDemandeCommandSerializer,
            serializers.PropositionIdentityDTOSerializer,
        ),
    }

    def get_operation_id(self, path, method):
        return 'pay_application_fees_after_request'


class PayApplicationFeesAfterRequestView(
    APIPermissionRequiredMixin,
    APIView,
):
    name = "pay_after_request"
    schema = PayApplicationFeesAfterRequestSchema()
    permission_mapping = {
        'POST': 'admission.pay_generaleducationadmission_fees_after_request',
    }

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])

    def post(self, request, *args, **kwargs):
        """Pay the application fee of the proposition after a manager request."""
        proposition_id = message_bus_instance.invoke(
            PayerFraisDossierPropositionSuiteDemandeCommand(uuid_proposition=str(self.kwargs['uuid']))
        )
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)
