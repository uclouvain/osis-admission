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
import uuid

from django.http import Http404
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.schema import AuthorizationAwareSchema
from admission.contrib.models import Scholarship, DiplomaticPost
from base.models.campus import Campus
from ddd.logic.shared_kernel.campus.commands import SearchUclouvainCampusesCommand, GetCampusCommand
from infrastructure.messages_bus import message_bus_instance


class RetrieveScholarshipView(RetrieveAPIView):
    """Retrieves a scholarship"""

    name = 'retrieve-scholarship'
    schema = AuthorizationAwareSchema()
    filter_backends = []
    serializer_class = serializers.ScholarshipSerializer
    queryset = Scholarship.objects.all()
    lookup_field = 'uuid'


class RetrieveCampusView(RetrieveAPIView):
    """Retrieves a campus"""

    name = 'retrieve-campus'
    schema = AuthorizationAwareSchema()
    filter_backends = []
    serializer_class = serializers.CampusSerializer

    def retrieve(self, request, **kwargs):
        try:
            campus = message_bus_instance.invoke(GetCampusCommand(uuid=kwargs.get('uuid')))
        except Campus.DoesNotExist:
            raise Http404
        serializer = serializers.CampusSerializer(instance=campus)
        return Response(serializer.data)


class ListCampusView(ListAPIView):
    """Retrieves the UCLouvain campuses"""

    name = 'list-campuses'
    schema = AuthorizationAwareSchema()
    filter_backends = []
    pagination_class = None
    serializer_class = serializers.CampusSerializer
    queryset = Campus.objects.none()
    ordered_campuses = {
        'LOUVAIN_LA_NEUVE_UUID': uuid.UUID('6f207107-bcf0-4b38-a622-9e78a3540c99'),
        'BRUXELLES_WOLUWE_UUID': uuid.UUID('6da2b1d8-d60a-4cca-b3c3-333b43529d11'),
        'BRUXELLES_SAINT_LOUIS_UUID': uuid.UUID('9e942dbe-45fc-4de7-9e17-ccd6e82345da'),
        'MONS_UUID': uuid.UUID('f2b2ac6f-1bde-4389-bd5e-2257407c10f5'),
        'BRUXELLES_SAINT_GILLES_UUID': uuid.UUID('f32a20cf-cfd6-47ab-b768-53c6c9df8b7c'),
        'TOURNAI_UUID': uuid.UUID('cf34ff38-268e-4c10-aaa3-ec0c76df2398'),
        'CHARLEROI_UUID': uuid.UUID('32bfcf4f-4b70-4532-9597-9722c61a27f5'),
        'NAMUR_UUID': uuid.UUID('ccdfd820-52dc-4aef-a325-fbba3a1f0f52'),
        'AUTRE_SITE_UUID': uuid.UUID('35b0431b-9609-4a31-a328-04c56571f4ba'),
    }
    campus_order_by_uuid = {
        campus_uuid: campus_index for campus_index, campus_uuid in enumerate(ordered_campuses.values())
    }

    def list(self, request, *args, **kwargs):
        campuses = message_bus_instance.invoke(SearchUclouvainCampusesCommand())
        campuses.sort(key=lambda campus: self.campus_order_by_uuid.get(campus.entity_id.uuid, 100))
        serializer = serializers.CampusSerializer(instance=campuses, many=True)
        return Response(serializer.data)


class RetrieveDiplomaticPostSchema(AuthorizationAwareSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        # Override the parameter type because every url parameter is considered as a string
        operation['parameters'][0]['schema']['type'] = 'integer'
        return operation


class RetrieveDiplomaticPostView(RetrieveAPIView):
    """Retrieves a diplomatic post"""

    name = 'retrieve-diplomatic-post'
    schema = RetrieveDiplomaticPostSchema()
    filter_backends = []
    serializer_class = serializers.DiplomaticPostSerializer
    queryset = DiplomaticPost.objects.annotate_countries().all()
    lookup_field = 'code'
