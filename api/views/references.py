# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.constants import ORDERED_CAMPUSES_UUIDS
from admission.models import DiplomaticPost
from base.models.campus import Campus
from ddd.logic.shared_kernel.campus.commands import (
    GetCampusQuery,
    SearchUclouvainCampusesQuery,
)
from infrastructure.messages_bus import message_bus_instance


@extend_schema_view(get=extend_schema(operation_id='retrieveCampus', tags=['campus']))
class RetrieveCampusView(RetrieveAPIView):
    """Retrieves a campus"""

    name = 'retrieve-campus'
    filter_backends = []
    serializer_class = serializers.CampusSerializer

    def retrieve(self, request, **kwargs):
        try:
            campus = message_bus_instance.invoke(GetCampusQuery(uuid=kwargs.get('uuid')))
        except Campus.DoesNotExist:
            raise Http404
        serializer = serializers.CampusSerializer(instance=campus)
        return Response(serializer.data)


@extend_schema_view(get=extend_schema(operation_id='listCampus', tags=['campus']))
class ListCampusView(ListAPIView):
    """Retrieves the UCLouvain campuses"""

    name = 'list-campuses'
    filter_backends = []
    pagination_class = None
    serializer_class = serializers.CampusSerializer
    queryset = Campus.objects.none()
    campus_order_by_uuid = {
        campus_uuid: campus_index for campus_index, campus_uuid in enumerate(ORDERED_CAMPUSES_UUIDS.values())
    }

    def list(self, request, *args, **kwargs):
        campuses = message_bus_instance.invoke(SearchUclouvainCampusesQuery())
        campuses.sort(key=lambda campus: self.campus_order_by_uuid.get(campus.uuid, 100))
        serializer = serializers.CampusSerializer(instance=campuses, many=True)
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(operation_id='retrieveDiplomaticPost', tags=['diplomatic-post']),
)
class RetrieveDiplomaticPostView(RetrieveAPIView):
    """Retrieves a diplomatic post"""

    name = 'retrieve-diplomatic-post'
    filter_backends = []
    serializer_class = serializers.DiplomaticPostSerializer
    queryset = DiplomaticPost.objects.annotate_countries().all()
    lookup_field = 'code'
