# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from admission.api import serializers


class DashboardViewSet(RetrieveAPIView):
    name = "dashboard"

    def get_queryset(self):
        # We must override this to bypass AssertionError from GenericAPIView
        return None

    @extend_schema(
        responses=serializers.DashboardSerializer,
        operation_id='retrieve_dashboard',
        tags=['propositions'],
    )
    def get(self, request, **kwargs):
        """Get the actions links for the application"""
        serializer = serializers.DashboardSerializer(
            instance={},
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)
