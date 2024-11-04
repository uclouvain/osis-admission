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
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.schema import ResponseSpecificSchema
from admission.ddd.parcours_doctoral.commands import RecupererAdmissionDoctoratQuery

from admission.utils import get_cached_admission_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class DoctorateSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.DoctorateDTOSerializer,
    }


class DoctorateAPIView(
    APIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    GenericAPIView,
):
    name = "doctorate"
    pagination_class = None
    filter_backends = []
    schema = DoctorateSchema()
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get the doctorate"""
        doctorate = message_bus_instance.invoke(
            RecupererAdmissionDoctoratQuery(doctorat_uuid=kwargs.get('uuid')),
        )
        serializer = serializers.DoctorateDTOSerializer(
            instance=doctorate,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)
