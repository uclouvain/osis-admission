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
from django.conf import settings
from django.db.models import (
    BooleanField,
    Exists,
    ExpressionWrapper,
    F,
    OuterRef,
    Q,
    TextField,
)
from django.utils.decorators import method_decorator
from django.utils.translation import get_language
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.filters import BaseFilterBackend
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.serializers import PersonSerializer
from admission.ddd.admission.doctorat.preparation.commands import (
    RechercherDoctoratQuery,
)
from admission.ddd.admission.domain.enums import LISTE_TYPES_FORMATION_GENERALE
from admission.ddd.admission.formation_continue.commands import (
    RechercherFormationContinueQuery,
)
from admission.ddd.admission.formation_generale.commands import (
    RechercherFormationGeneraleQuery,
)
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from admission.models import DiplomaticPost, EntityProxy
from base.auth.roles.tutor import Tutor
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import SECTOR
from base.models.person import Person
from base.models.specific_iufc_informations import SpecificIUFCInformations
from base.models.student import Student
from base.utils.cte import CTESubquery
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    "AutocompleteSectorView",
    "AutocompleteDoctoratView",
    "AutocompleteTutorView",
    "AutocompletePersonView",
    "AutocompleteGeneralEducationView",
    "AutocompleteContinuingEducationView",
    "AutocompleteDiplomaticPostView",
]


@extend_schema_view(get=extend_schema(operation_id='listSectorDTOs'))
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
        year = AnneeInscriptionFormationTranslator().recuperer(AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT)
        if not year:
            return Response([])
        doctorate_qs = EducationGroupYear.objects.annotate(
            path_as_string=CTESubquery(
                EntityVersion.objects.with_acronym_path(entity_id=OuterRef('management_entity')).values(
                    'path_as_string'
                )[:1],
                output_field=TextField(),
            ),
        ).filter(
            academic_year__year=year,
            education_group_type__category=Categories.TRAINING.name,
            education_group_type__name=TrainingType.PHD.name,
        )
        doctorate_paths = doctorate_qs.values_list('path_as_string', flat=True)
        # Get all sectors
        qs = (
            EntityProxy.objects.with_acronym()
            .with_title()
            .with_type()
            .filter(type=SECTOR)
            .annotate(
                sigle=F('acronym'),
                intitule=F('title'),  # TODO get translation when available
            )
            .values('sigle', 'intitule')
        )
        # Filter sectors by those which have doctorates
        filtered = [s for s in qs if any(s['sigle'] in path for path in doctorate_paths)]
        serializer = serializers.SectorDTOSerializer(instance=filtered, many=True)
        return Response(serializer.data)


class EducationSearchingBackendMixin:
    NAME_SCHEMA = {
        'name': 'acronym_or_name',
        'required': True,
        'in': 'query',
        'description': "The name or the acronym of the training",
        'schema': {
            'type': 'string',
        },
    }
    CAMPUS_SCHEMA = {
        'name': 'campus',
        'required': False,
        'in': 'query',
        'description': "The identifier of the campus where the training takes place",
        'schema': {
            'type': 'string',
        },
    }
    TRAINING_TYPE_SCHEMA = {
        'name': 'type',
        'required': True,
        'in': 'query',
        'description': "The type of the training",
        'schema': {
            'type': 'string',
            'enum': LISTE_TYPES_FORMATION_GENERALE,
        },
    }


class DoctorateEducationSearchingBackend(BaseFilterBackend, EducationSearchingBackendMixin):
    def get_schema_operation_parameters(self, view):  # pragma: no cover
        return [
            self.NAME_SCHEMA,
            self.CAMPUS_SCHEMA,
        ]


@extend_schema_view(get=extend_schema(operation_id='listDoctoratDTOs'))
class AutocompleteDoctoratView(ListAPIView):
    """Autocomplete doctorates given a sector"""

    name = "autocomplete-doctorate"
    pagination_class = None
    filter_backends = [DoctorateEducationSearchingBackend]
    serializer_class = serializers.DoctoratDTOSerializer

    def list(self, request, **kwargs):
        doctorat_list = message_bus_instance.invoke(
            RechercherDoctoratQuery(
                sigle_secteur_entite_gestion=kwargs.get('sigle'),
                terme_de_recherche=request.GET.get('acronym_or_name'),
                campus=request.GET.get('campus'),
            )
        )
        serializer = serializers.DoctoratDTOSerializer(instance=doctorat_list, many=True)
        return Response(serializer.data)


class GeneralEducationSearchingBackend(BaseFilterBackend, EducationSearchingBackendMixin):
    def get_schema_operation_parameters(self, view):  # pragma: no cover
        return [
            self.TRAINING_TYPE_SCHEMA,
            self.NAME_SCHEMA,
            self.CAMPUS_SCHEMA,
        ]


class ContinuingEducationSearchingBackend(BaseFilterBackend, EducationSearchingBackendMixin):
    def get_schema_operation_parameters(self, view):  # pragma: no cover
        return [
            self.NAME_SCHEMA,
            self.CAMPUS_SCHEMA,
        ]


@extend_schema_view(get=extend_schema(operation_id='listFormationGeneraleDTOs'))
class AutocompleteGeneralEducationView(ListAPIView):
    """Autocomplete to find a general education"""

    name = "autocomplete-general-education"
    serializer_class = serializers.FormationGeneraleDTOSerializer
    filter_backends = [GeneralEducationSearchingBackend]
    pagination_class = None

    def list(self, request, **kwargs):
        education_list = message_bus_instance.invoke(
            RechercherFormationGeneraleQuery(
                type_formation=request.GET.get('type'),
                campus=request.GET.get('campus'),
                terme_de_recherche=request.GET.get('acronym_or_name'),
            )
        )
        serializer = serializers.FormationGeneraleDTOSerializer(instance=education_list, many=True)
        return Response(serializer.data)


@extend_schema_view(get=extend_schema(operation_id='listFormationContinueDTOs'))
class AutocompleteContinuingEducationView(ListAPIView):
    """Autocomplete to find a continuing education"""

    name = "autocomplete-continuing-education"
    serializer_class = serializers.FormationContinueDTOSerializer
    filter_backends = [ContinuingEducationSearchingBackend]
    pagination_class = None

    def list(self, request, **kwargs):
        education_list = message_bus_instance.invoke(
            RechercherFormationContinueQuery(
                campus=request.GET.get('campus'),
                terme_de_recherche=request.GET.get('acronym_or_name'),
            )
        )

        # TODO to delete when old IUFC app is closed
        # Filter the list to retrieve only the trainings that are available
        if education_list:
            trainings_filters = Q()
            for education in education_list:
                trainings_filters |= Q(
                    training__academic_year__year=education.annee,
                    training__acronym=education.sigle,
                )

            opened_iufc_trainings = (
                SpecificIUFCInformations.objects.filter(show_to_candidate=True)
                .filter(trainings_filters)
                .values_list('training__acronym', 'training__academic_year__year')
            )

            opened_iufc_trainings_as_set = set(opened_iufc_trainings)

            education_list = [
                education
                for education in education_list
                if (education.sigle, education.annee) in opened_iufc_trainings_as_set
            ]

        serializer = serializers.FormationContinueDTOSerializer(instance=education_list, many=True)
        return Response(serializer.data)


class PersonSearchingBackend(BaseFilterBackend):
    searching_param = 'search'

    def filter_queryset(self, request, queryset, view):
        search_term = request.GET.get(self.searching_param, '')
        return queryset.filter(
            *[
                Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(global_id__icontains=search_term)
                for term in search_term.split()
            ],
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


class CampusSearchBackend(BaseFilterBackend):
    searching_param = 'search'

    def filter_queryset(self, request, queryset, view):
        search_term = request.GET.get(self.searching_param, '')

        return queryset.filter(Q(name__icontains=search_term))

    def get_schema_operation_parameters(self, view):  # pragma: no cover
        return [
            {
                'name': self.searching_param,
                'required': False,
                'in': 'query',
                'description': 'The term to search the campus on (its name)',
                'schema': {
                    'type': 'string',
                },
            },
        ]


@extend_schema_view(
    get=extend_schema(operation_id='listTutors'),
)
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


@extend_schema_view(
    get=extend_schema(operation_id='listPeople'),
)
class AutocompletePersonView(ListAPIView):
    """Autocomplete person"""

    name = "autocomplete-person"
    filter_backends = [PersonSearchingBackend]
    serializer_class = PersonSerializer
    queryset = (
        Person.objects.exclude(
            # Remove unexistent users
            Q(user_id__isnull=True)
            | Q(global_id='')
            | Q(global_id__isnull=True)
            | Q(first_name='')
            | Q(last_name='')
        )
        .alias(
            # Remove students who aren't tutors
            is_student_and_not_tutor=Exists(Student.objects.filter(person=OuterRef('pk'), person__tutor__isnull=True)),
        )
        .filter(is_student_and_not_tutor=False)
        .order_by('first_name', 'last_name')
    )


class DiplomaticPostSearchBackend(BaseFilterBackend):
    searching_param = 'search'
    country_param = 'country'

    def filter_queryset(self, request, queryset, view):
        search_term = request.GET.get(self.searching_param, '')
        country_term = request.GET.get(self.country_param, '')
        name_field = 'name_fr' if get_language() == settings.LANGUAGE_CODE_FR else 'name_en'

        if search_term:
            # Filter the queryset by name
            queryset = queryset.filter(**{f'{name_field}__icontains': search_term})

        if country_term:
            # Order the queryset to retrieve the diplomatic posts of the specified country first
            return queryset.annotate(
                in_specified_country=ExpressionWrapper(
                    Q(countries_iso_codes__contains=[country_term]),
                    output_field=BooleanField(),
                )
            ).order_by('-in_specified_country', name_field)

        return queryset.order_by(name_field)

    def get_schema_operation_parameters(self, view):  # pragma: no cover
        return [
            {
                'name': self.searching_param,
                'required': False,
                'in': 'query',
                'description': 'The term to search the diplomatic post on (its name)',
                'schema': {
                    'type': 'string',
                },
            },
            {
                'name': self.country_param,
                'required': False,
                'in': 'query',
                'description': 'If specified, the diplomatic posts of this country are returned first',
                'schema': {
                    'type': 'string',
                },
            },
        ]


@extend_schema_view(
    get=extend_schema(operation_id='listDiplomaticPosts'),
)
class AutocompleteDiplomaticPostView(ListAPIView):
    """Autocomplete diplomatic posts"""

    name = 'autocomplete-diplomatic-post'
    filter_backends = [DiplomaticPostSearchBackend]
    serializer_class = serializers.DiplomaticPostSerializer
    queryset = DiplomaticPost.objects.annotate_countries().all()
