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

from admission.api import serializers
from admission.api.schema import ResponseSpecificSchema
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.commands import (
    RecupererEpreuvesConfirmationQuery,
    SoumettreEpreuveConfirmationCommand,
    RecupererDerniereEpreuveConfirmationQuery,
)
from admission.utils import get_cached_admission_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class ConfirmationSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.ConfirmationPaperDTOSerializer,
    }

    def get_operation_id(self, path, method):
        if method == 'GET':
            return 'retrieve_confirmation_papers'
        return super().get_operation_id(path, method)


class ConfirmationAPIView(APIPermissionRequiredMixin, GenericAPIView):
    name = "confirmation"
    schema = ConfirmationSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission_confirmation',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get the confirmation papers related to the doctorate"""
        confirmation_papers = message_bus_instance.invoke(
            RecupererEpreuvesConfirmationQuery(doctorat_uuid=kwargs.get('uuid')),
        )
        serializer = serializers.ConfirmationPaperDTOSerializer(instance=confirmation_papers, many=True)
        return Response(serializer.data)


class LastConfirmationSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.ConfirmationPaperDTOSerializer,
        'PUT': (
            serializers.SubmitConfirmationPaperCommandSerializer,
            serializers.DoctorateIdentityDTOSerializer,
        ),
    }

    def get_operation_id(self, path, method):
        if method == 'GET':
            return 'retrieve_last_confirmation_paper'
        elif method == 'PUT':
            return 'submit_confirmation_paper'
        return super().get_operation_id(path, method)


class LastConfirmationAPIView(APIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "last_confirmation"
    schema = LastConfirmationSchema()
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission_confirmation',
        'PUT': 'admission.change_doctorateadmission_confirmation',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get the last confirmation paper related to the doctorate"""
        confirmation_paper = message_bus_instance.invoke(
            RecupererDerniereEpreuveConfirmationQuery(doctorat_uuid=kwargs.get('uuid')),
        )
        serializer = serializers.ConfirmationPaperDTOSerializer(instance=confirmation_paper)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """Submit the confirmation paper related to a doctorate"""
        serializer = serializers.SubmitConfirmationPaperCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        last_confirmation_paper = message_bus_instance.invoke(
            RecupererDerniereEpreuveConfirmationQuery(doctorat_uuid=kwargs.get('uuid')),
        )

        result = message_bus_instance.invoke(
            SoumettreEpreuveConfirmationCommand(
                uuid=last_confirmation_paper.uuid,
                **serializer.validated_data,
            )
        )

        serializer = serializers.DoctorateIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)
