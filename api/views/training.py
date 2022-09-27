# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.settings import api_settings

from admission.api.schema import ChoicesEnumSchema
from admission.api.serializers.activity import (
    DoctoralTrainingActivitySerializer,
    DoctoralTrainingAssentSerializer,
    DoctoralTrainingBatchSerializer,
    DoctoralTrainingConfigSerializer,
)
from admission.contrib.models.cdd_config import CddConfiguration
from admission.contrib.models.doctoral_training import Activity
from admission.ddd.doctorat.formation.commands import (
    DonnerAvisSurActiviteCommand,
    SoumettreActivitesCommand,
    SupprimerActiviteCommand,
)
from admission.utils import get_cached_admission_perm_obj
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class DoctoralTrainingSchema(ChoicesEnumSchema):
    operation_id_base = "_doctoral_training"

    def map_serializer(self, serializer):
        if isinstance(serializer, DoctoralTrainingActivitySerializer):
            possible_classes = serializer.serializer_class_mapping.values()
            if serializer.only_classes:
                # Only one of specified classes (for children)
                possible_classes = serializer.only_classes
            return {
                'oneOf': [self._get_reference(s()) for s in possible_classes],
                'discriminator': {'propertyName': 'object_type'},
            }
        return super().map_serializer(serializer)

    def get_components(self, path, method):
        components = super().get_components(path, method)
        for mapping_key, serializer in DoctoralTrainingActivitySerializer.serializer_class_mapping.items():
            # Specify the children classes if needed, by looking for parent category in the mapping key
            child_classes = DoctoralTrainingActivitySerializer.get_child_classes(mapping_key)

            serializer_dummy_instance = serializer(child_classes=child_classes)
            component_name = self.get_component_name(serializer_dummy_instance)
            components.setdefault(component_name, self.map_serializer(serializer_dummy_instance))
        return components


class DoctoralTrainingListView(APIPermissionRequiredMixin, GenericAPIView):
    name = "doctoral-training"
    pagination_class = None
    filter_backends = []
    serializer_class = DoctoralTrainingActivitySerializer
    schema = DoctoralTrainingSchema()
    lookup_field = 'uuid'
    lookup_url_kwarg = 'activity_id'
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission_doctoral_training',
        'POST': 'admission.add_doctorateadmission_doctoral_training',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get_queryset(self):
        return Activity.objects.filter(doctorate__uuid=self.kwargs['uuid']).prefetch_related('children')

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        admission = self.get_permission_object()
        data = {
            **request.data,
            'doctorate': admission.pk,
        }
        serializer = DoctoralTrainingActivitySerializer(admission=admission, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DoctoralTrainingConfigView(APIPermissionRequiredMixin, RetrieveModelMixin, GenericAPIView):
    name = "doctoral-training-config"
    pagination_class = None
    filter_backends = []
    serializer_class = DoctoralTrainingConfigSerializer
    lookup_field = 'uuid'
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission_doctoral_training',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get_object(self):
        management_entity_id = self.get_permission_object().doctorate.management_entity_id
        return CddConfiguration.objects.get_or_create(cdd_id=management_entity_id)[0]

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)


class DoctoralTrainingView(APIPermissionRequiredMixin, GenericAPIView):
    name = "doctoral-training"
    pagination_class = None
    filter_backends = []
    serializer_class = DoctoralTrainingActivitySerializer
    schema = DoctoralTrainingSchema()
    lookup_field = 'uuid'
    lookup_url_kwarg = 'activity_id'
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission_doctoral_training',
        'PUT': 'admission.view_doctorateadmission_doctoral_training',
        'DELETE': 'admission.delete_doctorateadmission_doctoral_training',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get_queryset(self):
        return Activity.objects.filter(doctorate__uuid=self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DoctoralTrainingActivitySerializer(instance, admission=self.get_permission_object())
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        data = {
            **request.data,
            'doctorate': self.get_permission_object().pk,
        }
        serializer = DoctoralTrainingActivitySerializer(instance, admission=self.get_permission_object(), data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        message_bus_instance.invoke(SupprimerActiviteCommand(activite_uuid=str(kwargs["activity_id"])))
        return Response(status=status.HTTP_204_NO_CONTENT)


class DoctoralTrainingBatchSchema(AutoSchema):
    def get_operation_id(self, path, method):
        return "submit_doctoral_training"


class DoctoralTrainingSubmitView(APIPermissionRequiredMixin, GenericAPIView):
    name = "doctoral-training-submit"
    pagination_class = None
    filter_backends = []
    serializer_class = DoctoralTrainingBatchSerializer
    schema = DoctoralTrainingBatchSchema()
    lookup_field = 'uuid'
    permission_mapping = {
        'POST': 'admission.submit_doctorateadmission_doctoral_training',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def post(self, request, *args, **kwargs):
        """Submit doctoral training activities."""
        serializer = DoctoralTrainingBatchSerializer(data=request.data)
        serializer.is_valid(True)
        cmd = SoumettreActivitesCommand(
            doctorat_uuid=self.kwargs['uuid'],
            activite_uuids=serializer.data['activity_uuids'],
        )
        try:
            message_bus_instance.invoke(cmd)
        except MultipleBusinessExceptions as exc:
            # Bypass normal exception handling to add activity_id to each error
            data = {
                api_settings.NON_FIELD_ERRORS_KEY: [
                    {
                        "status_code": exception.status_code,
                        "detail": exception.message,
                        "activite_id": str(exception.activite_id.uuid),
                    }
                    for exception in exc.exceptions
                ]
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DoctoralTrainingAssentSchema(AutoSchema):
    def get_operation_id(self, path, method):
        return "assent_doctoral_training"


class DoctoralTrainingAssentView(APIPermissionRequiredMixin, GenericAPIView):
    name = "doctoral-training-assent"
    pagination_class = None
    filter_backends = []
    serializer_class = DoctoralTrainingAssentSerializer
    schema = DoctoralTrainingAssentSchema()
    lookup_field = 'uuid'
    permission_mapping = {
        'POST': 'admission.assent_doctoral_training',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def post(self, request, *args, **kwargs):
        """Assent on a doctoral training activity."""
        serializer = DoctoralTrainingAssentSerializer(data=request.data)
        serializer.is_valid(True)
        cmd = DonnerAvisSurActiviteCommand(
            doctorat_uuid=self.kwargs['uuid'],
            activite_uuid=self.kwargs['activity_id'],
            **serializer.data,
        )
        message_bus_instance.invoke(cmd)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
