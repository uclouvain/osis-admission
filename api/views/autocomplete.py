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
from datetime import date

from django.db.models import F, OuterRef, Q, TextField
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.filters import BaseFilterBackend
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.serializers import PersonSerializer
from admission.contrib.models import EntityProxy
from admission.ddd.preparation.projet_doctoral.commands import (
    SearchDoctoratCommand,
)
from base.auth.roles.tutor import Tutor
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import SECTOR
from base.models.person import Person
from base.utils.cte import CTESubquery
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from infrastructure.messages_bus import message_bus_instance
from infrastructure.shared_kernel.academic_year.repository import academic_year as academic_year_repository


class AutocompleteSectorView(ListAPIView):
    """Autocomplete sectors"""
    name = "autocomplete-sector"
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.SectorDTOSerializer

    @method_decorator(cache_page(timeout=24 * 3600))
    def list(self, request, **kwargs):
        # TODO revert to command once it's in the shared kernel
        # Get all doctorates with their path (containing sector)
        year = GetCurrentAcademicYear().get_starting_academic_year(
            date.today(),
            academic_year_repository.AcademicYearRepository()
        ).year
        doctorate_qs = EducationGroupYear.objects.annotate(
            path_as_string=CTESubquery(
                EntityVersion.objects.with_acronym_path(
                    entity_id=OuterRef('management_entity'),
                ).values('path_as_string')[:1],
                output_field=TextField(),
            ),
        ).filter(
            academic_year__year=year,
            education_group_type__category=Categories.TRAINING.name,
            education_group_type__name=TrainingType.PHD.name,
        )
        doctorate_paths = doctorate_qs.values_list('path_as_string', flat=True)
        # Get all sectors
        qs = EntityProxy.objects.with_acronym().with_title().with_type().filter(type=SECTOR).annotate(
            sigle=F('acronym'),
            intitule_fr=F('title'),
            intitule_en=F('title'),  # TODO get translation when available
        ).values('sigle', 'intitule_fr', 'intitule_en')
        # Filter sectors by those which have doctorates
        filtered = [s for s in qs if any(s['sigle'] in path for path in doctorate_paths)]
        serializer = serializers.SectorDTOSerializer(instance=filtered, many=True)
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


class PersonSearchingBackend(BaseFilterBackend):
    searching_param = 'search'

    def filter_queryset(self, request, queryset, view):
        search_term = request.GET.get(self.searching_param, '')
        return queryset.filter(
            Q(first_name__icontains=search_term)
            | Q(last_name__icontains=search_term)
            | Q(global_id__contains=search_term)
        )

    def get_schema_operation_parameters(self, view):  # pragma: no cover
        return [
            {
                'name': self.searching_param,
                'required': True,
                'in': 'query',
                'description': "The term to search the persons on (first or last name, or global id)",
                'schema': {
                    'type': 'string',
                },
            },
        ]


class AutocompleteTutorView(ListAPIView):
    """Autocomplete tutors"""

    name = "autocomplete-tutor"
    filter_backends = [PersonSearchingBackend]
    serializer_class = serializers.TutorSerializer
    queryset = (
        Tutor.objects.annotate(
            first_name=F("person__first_name"),
            last_name=F("person__last_name"),
            global_id=F("person__global_id"),
        )
        .exclude(Q(person__user_id__isnull=True) | Q(person__global_id=''))
        .distinct('global_id')
        .select_related("person")
    )


class AutocompletePersonView(ListAPIView):
    """Autocomplete person"""

    name = "autocomplete-person"
    filter_backends = [PersonSearchingBackend]
    serializer_class = PersonSerializer
    queryset = Person.objects.exclude(Q(user_id__isnull=True) | Q(global_id=''))
