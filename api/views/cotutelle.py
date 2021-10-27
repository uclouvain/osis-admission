# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.preparation.projet_doctoral.commands import DefinirCotutelleCommand, GetCotutelleCommand
from infrastructure.messages_bus import message_bus_instance


class CotutelleSchema(ResponseSpecificSchema):
    operation_id_base = '_cotutelle'
    serializer_mapping = {
        'GET': serializers.CotutelleDTOSerializer,
        'PUT': (serializers.DefinirCotutelleCommandSerializer, serializers.PropositionIdentityDTOSerializer),
    }


class CotutelleAPIView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericAPIView):
    name = "cotutelle"
    schema = CotutelleSchema()
    pagination_class = None
    filter_backends = []

    def get(self, request, *args, **kwargs):
        """Get the cotutelle of a proposition"""
        # TODO call osis_role perm for this object
        cotutelle = message_bus_instance.invoke(
            GetCotutelleCommand(uuid_proposition=kwargs.get('uuid'))
        )
        serializer = serializers.CotutelleDTOSerializer(instance=cotutelle)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """Set the cotutelle of a proposition"""
        data = {'uuid_proposition': str(kwargs['uuid']), **request.data}
        serializer = serializers.DefinirCotutelleCommandSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(DefinirCotutelleCommand(**serializer.data))
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)
