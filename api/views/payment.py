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
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from admission.api import serializers
from admission.api.schema import ResponseSpecificSchema
from admission.ddd.admission.formation_generale.commands import (
    SpecifierPaiementVaEtreOuvertParCandidatCommand,
    RecupererListePaiementsPropositionQuery,
)
from admission.utils import get_cached_general_education_admission_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    'OpenApplicationFeesPaymentView',
    'ApplicationFeesListView',
]


class OpenApplicationFeesPaymentSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'POST': (
            serializers.SpecifierPaiementVaEtreOuvertParCandidatCommandSerializer,
            serializers.PaiementDTOSerializer,
        ),
        'PUT': (
            serializers.SpecifierPaiementVaEtreOuvertParCandidatCommandSerializer,
            serializers.PaiementDTOSerializer,
        ),
    }

    def get_operation_id(self, path, method):
        return {
            'POST': 'open_application_fees_payment_after_submission',
            'PUT': 'open_application_fees_payment_after_request',
        }[method]


class OpenApplicationFeesPaymentView(
    APIPermissionRequiredMixin,
    APIView,
):
    name = "open_application_fees_payment"
    schema = OpenApplicationFeesPaymentSchema()
    permission_mapping = {
        'POST': 'admission.pay_generaleducationadmission_fees',
        'PUT': 'admission.pay_generaleducationadmission_fees_after_request',
    }
    serializer_class = serializers.PaiementDTOSerializer

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])

    def post(self, request, *args, **kwargs):
        """Open the payment of the application fee of the proposition after its submission."""
        created_payment = message_bus_instance.invoke(
            SpecifierPaiementVaEtreOuvertParCandidatCommand(uuid_proposition=str(self.kwargs['uuid']))
        )
        serializer = self.serializer_class(instance=created_payment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        """Open the payment of the application fee of the proposition after a manager request."""
        return self.post(request, *args, **kwargs)


class ApplicationFeesListSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.PaiementDTOSerializer,
    }

    def get_operation_id(self, path, method):
        return 'list_application_fees_payments'


class ApplicationFeesListView(APIPermissionRequiredMixin, ListAPIView):
    name = "view_application_fees"
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission_fees',
    }
    serializer_class = serializers.PaiementDTOSerializer
    pagination_class = None
    filter_backends = []
    schema = ApplicationFeesListSchema()

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])

    def list(self, request, *args, **kwargs):
        application_fees = message_bus_instance.invoke(
            RecupererListePaiementsPropositionQuery(uuid_proposition=str(self.kwargs['uuid']))
        )
        serializer = serializers.PaiementDTOSerializer(
            instance=application_fees,
            many=True,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
