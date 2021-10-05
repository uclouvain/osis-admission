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
from django.db.models import F
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema

from admission.api import serializers
from admission.contrib.models import EntityProxy
from base.models.enums.entity_type import SECTOR
from admission.ddd.preparation.projet_doctoral.commands import SearchDoctoratCommand
from infrastructure.messages_bus import message_bus_instance
from reference.models.country import Country


class AutocompleteCountryView(ListAPIView):
    """Autocomplete country"""
    name = "countries"
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.CountrySerializer
    queryset = Country.objects.all()
    schema = AutoSchema(operation_id_base='Countries')


class AutocompleteSectorView(ListAPIView):
    """Autocomplete sectors"""
    name = "autocomplete-sector"
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.SectorDTOSerializer

    def list(self, request, **kwargs):
        # TODO revert to command once it's in the shared kernel
        qs = EntityProxy.objects.with_acronym().with_title().with_type().filter(type=SECTOR).annotate(
            sigle=F('acronym'),
            intitule_fr=F('title'),
            intitule_en=F('title'),
        ).values('sigle', 'intitule_fr', 'intitule_en')
        serializer = serializers.SectorDTOSerializer(instance=qs, many=True)
        return Response(serializer.data)


class AutocompleteDoctoratView(ListAPIView):
    """Autocomplete doctorates given a sector"""
    name = "autocomplete-doctorate"
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.DoctoratDTOSerializer

    def list(self, request, **kwargs):
        doctorat_list = message_bus_instance.invoke(
            SearchDoctoratCommand(sigle_secteur_entite_gestion=kwargs.get('sigle'))
        )
        serializer = serializers.DoctoratDTOSerializer(instance=doctorat_list, many=True)
        return Response(serializer.data)
