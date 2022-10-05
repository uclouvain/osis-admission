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
from admission.ddd.parcours_doctoral.commands import RecupererDoctoratQuery
from admission.ddd.parcours_doctoral.epreuve_confirmation.commands import (
    CompleterEpreuveConfirmationParPromoteurCommand,
    RecupererDerniereEpreuveConfirmationQuery,
    RecupererEpreuvesConfirmationQuery,
    SoumettreEpreuveConfirmationCommand,
    SoumettreReportDeDateCommand,
)
from admission.ddd.admission.doctorat.preparation.commands import GetGroupeDeSupervisionCommand
from admission.exports.admission_confirmation_canvas import admission_pdf_confirmation_canvas
from admission.utils import get_cached_admission_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    "ConfirmationAPIView",
    "LastConfirmationAPIView",
    "LastConfirmationCanvasAPIView",
    "SupervisedConfirmationAPIView",
]


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
        'POST': (
            serializers.SubmitConfirmationPaperExtensionRequestCommandSerializer,
            serializers.DoctorateIdentityDTOSerializer,
        ),
        'PUT': (
            serializers.SubmitConfirmationPaperCommandSerializer,
            serializers.DoctorateIdentityDTOSerializer,
        ),
    }

    def get_operation_id(self, path, method):
        if method == 'GET':
            return 'retrieve_last_confirmation_paper'
        elif method == 'POST':
            return 'submit_confirmation_paper_extension_request'
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
        'POST': 'admission.change_doctorateadmission_confirmation_extension',
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

    def post(self, request, *args, **kwargs):
        """Submit the extension request of the last confirmation paper of a doctorate"""
        serializer = serializers.SubmitConfirmationPaperExtensionRequestCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        last_confirmation_paper = message_bus_instance.invoke(
            RecupererDerniereEpreuveConfirmationQuery(doctorat_uuid=kwargs.get('uuid')),
        )

        result = message_bus_instance.invoke(
            SoumettreReportDeDateCommand(
                uuid=last_confirmation_paper.uuid,
                **serializer.validated_data,
            )
        )

        serializer = serializers.DoctorateIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)


class LastConfirmationCanvasSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.ConfirmationPaperCanvasSerializer,
    }

    def get_operation_id(self, path, method):
        return 'retrieve_last_confirmation_paper_canvas'


class LastConfirmationCanvasAPIView(APIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "last_confirmation_canvas"
    schema = LastConfirmationCanvasSchema()
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission_confirmation',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get the last confirmation paper canvas related to the doctorate"""
        doctorate, confirmation_paper, supervision_group = message_bus_instance.invoke_multiple(
            [
                RecupererDoctoratQuery(self.kwargs.get('uuid')),
                RecupererDerniereEpreuveConfirmationQuery(doctorat_uuid=kwargs.get('uuid')),
                GetGroupeDeSupervisionCommand(uuid_proposition=self.kwargs.get('uuid')),
            ]
        )
        admission = self.get_permission_object()

        uuid = admission_pdf_confirmation_canvas(
            admission=admission,
            language=admission.candidate.language,
            context={
                'doctorate': doctorate,
                'confirmation_paper': confirmation_paper,
                'supervision_group': supervision_group,
                'supervision_people_nb': (
                    len(supervision_group.signatures_promoteurs) + len(supervision_group.signatures_membres_CA)
                ),
            },
        )

        serializer = serializers.ConfirmationPaperCanvasSerializer(instance={'uuid': uuid})

        return Response(serializer.data)


class PromoterConfirmationSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'PUT': (
            serializers.CompleteConfirmationPaperByPromoterCommandSerializer,
            serializers.DoctorateIdentityDTOSerializer,
        ),
    }

    def get_operation_id(self, path, method):
        return 'complete_confirmation_paper_by_promoter'


class SupervisedConfirmationAPIView(
    APIPermissionRequiredMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    name = "supervised_confirmation"
    schema = PromoterConfirmationSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'PUT': 'admission.upload_pdf_confirmation',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def put(self, request, *args, **kwargs):
        """Complete the confirmation paper related to a doctorate"""
        serializer = serializers.CompleteConfirmationPaperByPromoterCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        last_confirmation_paper = message_bus_instance.invoke(
            RecupererDerniereEpreuveConfirmationQuery(doctorat_uuid=kwargs.get('uuid')),
        )

        result = message_bus_instance.invoke(
            CompleterEpreuveConfirmationParPromoteurCommand(
                uuid=last_confirmation_paper.uuid,
                **serializer.validated_data,
            )
        )

        serializer = serializers.DoctorateIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)
