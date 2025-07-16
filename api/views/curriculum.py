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

from collections import defaultdict
from functools import partial
from typing import Union

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import OuterRef, Q, Subquery
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import RetrieveAPIView, get_object_or_404
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from admission.api import serializers
from admission.api.permissions import IsSelfPersonTabOrTabPermission
from admission.api.serializers import ProfessionalExperienceSerializer
from admission.api.serializers.curriculum import EducationalExperienceSerializer
from admission.api.views.mixins import (
    ContinuingEducationPersonRelatedMixin,
    GeneralEducationPersonRelatedMixin,
    PersonRelatedMixin,
)
from admission.api.views.submission import SubmitPropositionMixin
from admission.ddd.admission.doctorat.preparation import commands as doctorate_commands
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AnneesCurriculumNonSpecifieesException,
    ExperiencesAcademiquesNonCompleteesException,
    ExperiencesNonAcademiquesCertificatManquantException,
)
from admission.ddd.admission.formation_continue import commands as continuing_commands
from admission.ddd.admission.formation_generale import commands as general_commands
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
from osis_profile.models import (
    EducationalExperience,
    EducationalExperienceYear,
    ProfessionalExperience,
)
from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    "PersonCurriculumView",
    "DoctorateCurriculumView",
    "ExperienceViewSet",
    "ProfessionalExperienceViewSet",
    "CommonProfessionalExperienceViewSet",
    "EducationalExperienceViewSet",
    "CommonEducationalExperienceViewSet",
    "GeneralCurriculumView",
    "GeneralEducationalExperienceViewSet",
    "GeneralProfessionalExperienceViewSet",
    "ContinuingCurriculumView",
    "ContinuingEducationalExperienceViewSet",
    "ContinuingProfessionalExperienceViewSet",
]

GENERAL_EDUCATION_PERMISSIONS_MAPPING = {
    'GET': 'admission.view_generaleducationadmission_curriculum',
    'POST': 'admission.change_generaleducationadmission_curriculum',
    'PUT': 'admission.change_generaleducationadmission_curriculum',
    'DELETE': 'admission.change_generaleducationadmission_curriculum',
}

CONTINUING_EDUCATION_PERMISSIONS_MAPPING = {
    'GET': 'admission.view_continuingeducationadmission_curriculum',
    'POST': 'admission.change_continuingeducationadmission_curriculum',
    'PUT': 'admission.change_continuingeducationadmission_curriculum',
    'DELETE': 'admission.change_continuingeducationadmission_curriculum',
}

DOCTORATE_PERMISSIONS_MAPPING = {
    'GET': 'admission.view_admission_curriculum',
    'POST': 'admission.change_admission_curriculum',
    'PUT': 'admission.change_admission_curriculum',
    'PATCH': 'admission.change_admission_curriculum',
    'DELETE': 'admission.change_admission_curriculum',
}


class BaseCurriculumView(APIPermissionRequiredMixin, RetrieveAPIView):
    pagination_class = None
    filter_backends = []
    queryset = []
    check_command_class = None
    extra_serializer_context = {}

    def get(self, request, *args, **kwargs):
        """Return the curriculum experiences of a person with the mandatory years to complete."""
        current_person = self.get_object()
        professional_experiences = (
            ProfessionalExperience.objects.filter(person=current_person)
            .annotate(
                valuated_from_trainings=ArrayAgg(
                    'valuated_from_admission__training__education_group_type__name',
                    filter=Q(valuated_from_admission__isnull=False),
                ),
            )
            .order_by('-start_date', '-end_date')
        )

        educational_experiences = (
            EducationalExperience.objects.filter(person=current_person)
            .annotate(
                last_academic_year=Subquery(
                    EducationalExperienceYear.objects.filter(educational_experience_id=OuterRef("pk")).values(
                        "academic_year__year"
                    )[:1]
                ),
                valuated_from_trainings=ArrayAgg(
                    'valuated_from_admission__training__education_group_type__name',
                    filter=Q(valuated_from_admission__isnull=False),
                ),
            )
            .order_by("-last_academic_year")
        )

        incomplete_periods = []
        incomplete_experiences = defaultdict(list)
        incomplete_professional_experiences = defaultdict(list)
        if self.check_command_class:
            try:
                message_bus_instance.invoke(self.check_command_class(uuid_proposition=self.kwargs.get('uuid')))
            except MultipleBusinessExceptions as exc:
                missing_year_exceptions = []
                for exception in exc.exceptions:
                    if isinstance(exception, ExperiencesAcademiquesNonCompleteesException):
                        incomplete_experiences[exception.reference].append(exception.message)
                    elif isinstance(exception, AnneesCurriculumNonSpecifieesException):
                        missing_year_exceptions.append(exception)
                    elif isinstance(exception, ExperiencesNonAcademiquesCertificatManquantException):
                        incomplete_professional_experiences[exception.reference].append(exception.message)
                incomplete_periods = [
                    e.message
                    for e in sorted(missing_year_exceptions, key=lambda exception: exception.periode[0], reverse=True)
                ]

        serializer = serializers.CurriculumDetailsSerializer(
            instance={
                'professional_experiences': professional_experiences,
                'educational_experiences': educational_experiences,
                'file': current_person,
                'incomplete_periods': incomplete_periods,
                'incomplete_experiences': incomplete_experiences,
                'incomplete_professional_experiences': incomplete_professional_experiences,
            },
            context={
                'related_person': current_person,
                **self.extra_serializer_context,
            },
        )

        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(operation_id='retrieveCurriculumDetails', tags=['person']),
)
class PersonCurriculumView(PersonRelatedMixin, BaseCurriculumView):
    name = 'curriculum'
    permission_classes = [partial(IsSelfPersonTabOrTabPermission, permission_suffix="curriculum")]
    serializer_class = serializers.CurriculumDetailsSerializer


class CurriculumView(SubmitPropositionMixin, BaseCurriculumView):
    complete_command_class = None
    serializer_mapping = {}

    def get_serializer_class(self):
        return self.serializer_mapping.get(self.request.method)

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        message_bus_instance.invoke(
            self.complete_command_class(**serializer.data, auteur_modification=request.user.person.global_id)
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        data = {**serializer.data, 'errors': self.get_permission_object().detailed_status}
        self.add_access_conditions_url(data)
        return Response(data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(operation_id='retrieveCurriculumDetailsAdmission', tags=['person']),
    put=extend_schema(operation_id='updateDoctoratCompleterCurriculumCommandAdmission', tags=['person']),
)
class DoctorateCurriculumView(PersonRelatedMixin, CurriculumView):
    name = "doctorate_curriculum"
    permission_mapping = DOCTORATE_PERMISSIONS_MAPPING
    check_command_class = doctorate_commands.VerifierCurriculumQuery
    complete_command_class = doctorate_commands.CompleterCurriculumCommand
    serializer_mapping = {
        'PUT': serializers.DoctoratCompleterCurriculumCommandSerializer,
        'GET': serializers.CurriculumDetailsSerializer,
    }


@extend_schema_view(
    get=extend_schema(operation_id='retrieveCurriculumDetailsGeneralEducationAdmission', tags=['person']),
    put=extend_schema(operation_id='updateGeneralEducationCompleterCurriculumCommandAdmission', tags=['person']),
)
class GeneralCurriculumView(GeneralEducationPersonRelatedMixin, CurriculumView):
    name = "general_curriculum"
    permission_mapping = GENERAL_EDUCATION_PERMISSIONS_MAPPING
    check_command_class = general_commands.VerifierCurriculumQuery
    complete_command_class = general_commands.CompleterCurriculumCommand
    serializer_mapping = {
        'PUT': serializers.GeneralEducationCompleterCurriculumCommandSerializer,
        'GET': serializers.CurriculumDetailsSerializer,
    }
    extra_serializer_context = {
        'current_academic_year_start_month_is_facultative': True,
    }


@extend_schema_view(
    get=extend_schema(operation_id='retrieveCurriculumDetailsContinuingEducationAdmission', tags=['person']),
    put=extend_schema(operation_id='updateContinuingEducationCompleterCurriculumCommandAdmission', tags=['person']),
)
class ContinuingCurriculumView(ContinuingEducationPersonRelatedMixin, CurriculumView):
    name = "continuing_curriculum"
    permission_mapping = CONTINUING_EDUCATION_PERMISSIONS_MAPPING
    complete_command_class = continuing_commands.CompleterCurriculumCommand
    serializer_mapping = {
        'PUT': serializers.ContinuingEducationCompleterCurriculumCommandSerializer,
        'GET': serializers.CurriculumDetailsSerializer,
    }


@extend_schema_view(
    retrieve=extend_schema(
        parameters=[OpenApiParameter(name="experience_id", type=OpenApiTypes.UUID, location=OpenApiParameter.PATH)],
        tags=['person'],
    ),
)
class ExperienceViewSet(
    APIPermissionRequiredMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'experience_id'
    http_method_names = [m for m in ModelViewSet.http_method_names if m not in {'patch'}]

    pagination_class = None
    filter_backends = []
    model = None

    def get_queryset(self):
        return (
            self.model.objects.filter(person=self.candidate).annotate(
                valuated_from_trainings=ArrayAgg(
                    'valuated_from_admission__training__education_group_type__name',
                    filter=Q(valuated_from_admission__isnull=False),
                ),
            )
            if self.kwargs.get('uuid')
            else self.model.objects.none()
        )

    @cached_property
    def experience(self) -> Union[ProfessionalExperience, EducationalExperience]:
        """Get the current experience from its uuid."""
        return get_object_or_404(queryset=self.get_queryset(), uuid=self.kwargs.get('experience_id'))

    def get_object(self):
        return self.experience

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.kwargs.get('uuid'):
            context['candidate'] = self.candidate
        return context

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status(request.user.person)
        return response

    def _check_perms_update(self):
        if self.experience.valuated_from_trainings or self.experience.external_id:
            raise PermissionDenied(_("This experience cannot be updated as it has already been valuated."))

    @extend_schema(
        parameters=[OpenApiParameter(name="experience_id", type=OpenApiTypes.UUID, location=OpenApiParameter.PATH)],
        tags=['person'],
    )
    def update(self, request, *args, **kwargs):
        self._check_perms_update()
        response = super().update(request, *args, **kwargs)
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status(request.user.person)
        return response

    @extend_schema(
        parameters=[OpenApiParameter(name="experience_id", type=OpenApiTypes.UUID, location=OpenApiParameter.PATH)],
        tags=['person'],
    )
    def destroy(self, request, *args, **kwargs):
        if self.experience.valuated_from_trainings or self.experience.external_id:
            raise PermissionDenied(_("This experience cannot be updated as it has already been valuated."))

        response = super().destroy(request, *args, **kwargs)
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status(request.user.person)
        return response


class BaseProfessionalExperienceViewSet(ExperienceViewSet):
    model = ProfessionalExperience
    serializer_class = ProfessionalExperienceSerializer

    def _check_perms_update(self):
        is_valuated_in_doctorates = any(
            training_type in AnneeInscriptionFormationTranslator.DOCTORATE_EDUCATION_TYPES
            for training_type in self.experience.valuated_from_trainings
        )
        is_valuated_in_general_educations = any(
            training_type in AnneeInscriptionFormationTranslator.GENERAL_EDUCATION_TYPES
            for training_type in self.experience.valuated_from_trainings
        )
        is_certificate_missing = not self.experience.certificate

        if (
            self.experience.certificate and (is_valuated_in_doctorates or is_valuated_in_general_educations)
            or (self.experience.external_id and not is_certificate_missing)
        ):
            raise PermissionDenied(_("This experience cannot be updated as it has already been valuated."))


@extend_schema_view(
    create=extend_schema(operation_id='createProfessionalExperienceAdmission', tags=['person']),
    retrieve=extend_schema(operation_id='retrieveProfessionalExperienceAdmission', tags=['person']),
    update=extend_schema(operation_id='updateProfessionalExperienceAdmission', tags=['person']),
    destroy=extend_schema(operation_id='destroyProfessionalExperienceAdmission', tags=['person']),
)
class ProfessionalExperienceViewSet(PersonRelatedMixin, BaseProfessionalExperienceViewSet):
    name = "doctorate_professional_experiences"
    permission_classes = [partial(IsSelfPersonTabOrTabPermission, permission_suffix="curriculum")]

    def get_object(self):
        return self.experience


@extend_schema_view(
    create=extend_schema(operation_id='createProfessionalExperience', tags=['person']),
    retrieve=extend_schema(operation_id='retrieveProfessionalExperience', tags=['person']),
    update=extend_schema(operation_id='updateProfessionalExperience', tags=['person']),
    destroy=extend_schema(operation_id='destroyProfessionalExperience', tags=['person']),
)
class CommonProfessionalExperienceViewSet(ProfessionalExperienceViewSet):
    name = "professional_experiences"


@extend_schema_view(
    create=extend_schema(operation_id='createProfessionalExperienceGeneralEducationAdmission', tags=['person']),
    retrieve=extend_schema(operation_id='retrieveProfessionalExperienceGeneralEducationAdmission', tags=['person']),
    update=extend_schema(operation_id='updateProfessionalExperienceGeneralEducationAdmission', tags=['person']),
    destroy=extend_schema(operation_id='destroyProfessionalExperienceGeneralEducationAdmission', tags=['person']),
)
class GeneralProfessionalExperienceViewSet(GeneralEducationPersonRelatedMixin, BaseProfessionalExperienceViewSet):
    name = "general_professional_experiences"
    permission_mapping = GENERAL_EDUCATION_PERMISSIONS_MAPPING

    def get_object(self):
        return self.experience


@extend_schema_view(
    create=extend_schema(operation_id='createProfessionalExperienceContinuingEducationAdmission', tags=['person']),
    retrieve=extend_schema(operation_id='retrieveProfessionalExperienceContinuingEducationAdmission', tags=['person']),
    update=extend_schema(operation_id='updateProfessionalExperienceContinuingEducationAdmission', tags=['person']),
    destroy=extend_schema(operation_id='destroyProfessionalExperienceContinuingEducationAdmission', tags=['person']),
)
class ContinuingProfessionalExperienceViewSet(ContinuingEducationPersonRelatedMixin, BaseProfessionalExperienceViewSet):
    name = "continuing_professional_experiences"
    permission_mapping = CONTINUING_EDUCATION_PERMISSIONS_MAPPING

    def get_object(self):
        return self.experience


class BaseEducationalExperienceViewSet(ExperienceViewSet):
    model = EducationalExperience
    serializer_class = EducationalExperienceSerializer


@extend_schema_view(
    create=extend_schema(operation_id='createEducationalExperienceAdmission', tags=['person']),
    retrieve=extend_schema(operation_id='retrieveEducationalExperienceAdmission', tags=['person']),
    update=extend_schema(operation_id='updateEducationalExperienceAdmission', tags=['person']),
    destroy=extend_schema(operation_id='destroyEducationalExperienceAdmission', tags=['person']),
)
class EducationalExperienceViewSet(PersonRelatedMixin, BaseEducationalExperienceViewSet):
    name = "doctorate_educational_experiences"
    permission_classes = [partial(IsSelfPersonTabOrTabPermission, permission_suffix="curriculum")]

    def _check_perms_update(self):
        # With doctorate
        if (
            any(
                training_type in AnneeInscriptionFormationTranslator.DOCTORATE_EDUCATION_TYPES
                for training_type in self.experience.valuated_from_trainings
            )
            or self.experience.external_id
        ):
            raise PermissionDenied(_("This experience cannot be updated as it has already been valuated."))

    def get_object(self):
        return self.experience


@extend_schema_view(
    create=extend_schema(operation_id='createEducationalExperience', tags=['person']),
    retrieve=extend_schema(operation_id='retrieveEducationalExperience', tags=['person']),
    update=extend_schema(operation_id='updateEducationalExperience', tags=['person']),
    destroy=extend_schema(operation_id='destroyEducationalExperience', tags=['person']),
)
class CommonEducationalExperienceViewSet(EducationalExperienceViewSet):
    name = "educational_experiences"


@extend_schema_view(
    create=extend_schema(operation_id='createEducationalExperienceGeneralEducationAdmission', tags=['person']),
    retrieve=extend_schema(operation_id='retrieveEducationalExperienceGeneralEducationAdmission', tags=['person']),
    update=extend_schema(operation_id='updateEducationalExperienceGeneralEducationAdmission', tags=['person']),
    destroy=extend_schema(operation_id='destroyEducationalExperienceGeneralEducationAdmission', tags=['person']),
)
class GeneralEducationalExperienceViewSet(GeneralEducationPersonRelatedMixin, BaseEducationalExperienceViewSet):
    name = "general_educational_experiences"
    permission_mapping = GENERAL_EDUCATION_PERMISSIONS_MAPPING

    def _check_perms_update(self):
        if (
            not all(
                training_type in AnneeInscriptionFormationTranslator.CONTINUING_EDUCATION_TYPES
                for training_type in self.experience.valuated_from_trainings
            )
            or self.experience.external_id
        ):
            raise PermissionDenied(_("This experience cannot be updated as it has already been valuated."))

    def get_object(self):
        return self.experience


@extend_schema_view(
    create=extend_schema(operation_id='createEducationalExperienceContinuingEducationAdmission', tags=['person']),
    retrieve=extend_schema(operation_id='retrieveEducationalExperienceContinuingEducationAdmission', tags=['person']),
    update=extend_schema(operation_id='updateEducationalExperienceContinuingEducationAdmission', tags=['person']),
    destroy=extend_schema(operation_id='destroyEducationalExperienceContinuingEducationAdmission', tags=['person']),
)
class ContinuingEducationalExperienceViewSet(ContinuingEducationPersonRelatedMixin, BaseEducationalExperienceViewSet):
    name = "continuing_educational_experiences"
    permission_mapping = CONTINUING_EDUCATION_PERMISSIONS_MAPPING

    def get_object(self):
        return self.experience
