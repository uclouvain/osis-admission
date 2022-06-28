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
from rest_framework.response import Response

from admission.api.schema import ChoicesEnumSchema
from admission.api.serializers.training import DoctoralTrainingActivitySerializer
from admission.contrib.models.doctoral_training import Activity
from admission.utils import get_cached_admission_perm_obj
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
            child_classes = self._get_child_classes(mapping_key)

            serializer_dummy_instance = serializer(child_classes=child_classes)
            component_name = self.get_component_name(serializer_dummy_instance)
            components.setdefault(component_name, self.map_serializer(serializer_dummy_instance))
        return components

    @staticmethod
    def _get_child_classes(mapping_key):
        child_classes = []
        for key, value in DoctoralTrainingActivitySerializer.serializer_class_mapping.items():
            if not isinstance(mapping_key, tuple) and isinstance(key, tuple) and key[0] == mapping_key:
                child_classes.append(value)
        if child_classes:
            return child_classes


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
        data = {
            **request.data,
            'doctorate': self.get_permission_object().pk,
        }
        serializer = DoctoralTrainingActivitySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get_queryset(self):
        return Activity.objects.filter(doctorate__uuid=self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DoctoralTrainingActivitySerializer(instance)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        data = {
            **request.data,
            'doctorate': self.get_permission_object().pk,
        }
        serializer = DoctoralTrainingActivitySerializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
