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

from collections import defaultdict
from functools import partial
from typing import Union

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Subquery, OuterRef, Q
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404, RetrieveAPIView
from rest_framework.mixins import UpdateModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from admission.api import serializers
from admission.api.permissions import IsSelfPersonTabOrTabPermission
from admission.api.serializers import ProfessionalExperienceSerializer
from admission.api.serializers.curriculum import EducationalExperienceSerializer
from admission.api.views.mixins import (
    PersonRelatedMixin,
    GeneralEducationPersonRelatedMixin,
    ContinuingEducationPersonRelatedMixin,
    SpecificPersonRelatedSchema,
)
from admission.api.views.submission import SubmitPropositionMixin
from admission.ddd.admission.doctorat.preparation import commands as doctorate_commands
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    ExperiencesAcademiquesNonCompleteesException,
    AnneesCurriculumNonSpecifieesException,
)
from admission.ddd.admission.formation_generale import commands as general_commands
from admission.ddd.admission.formation_continue import commands as continuing_commands
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
from osis_profile.models import ProfessionalExperience, EducationalExperience, EducationalExperienceYear
from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    "PersonCurriculumView",
    "DoctorateCurriculumView",
    "ExperienceViewSet",
    "ProfessionalExperienceViewSet",
    "EducationalExperienceViewSet",
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
            },
            context={
                'related_person': current_person,
            },
        )

        return Response(serializer.data)


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
        message_bus_instance.invoke(self.complete_command_class(**serializer.data))
        self.get_permission_object().update_detailed_status(request.user.person)
        data = {**serializer.data, 'errors': self.get_permission_object().detailed_status}
        self.add_access_conditions_url(data)
        return Response(data, status=status.HTTP_200_OK)


class DoctorateCurriculumView(PersonRelatedMixin, CurriculumView):
    name = "doctorate_curriculum"
    permission_mapping = DOCTORATE_PERMISSIONS_MAPPING
    check_command_class = doctorate_commands.VerifierCurriculumQuery
    complete_command_class = doctorate_commands.CompleterCurriculumCommand
    schema = SpecificPersonRelatedSchema()
    serializer_mapping = {
        'PUT': serializers.DoctoratCompleterCurriculumCommandSerializer,
        'GET': serializers.CurriculumDetailsSerializer,
    }


class GeneralCurriculumView(GeneralEducationPersonRelatedMixin, CurriculumView):
    name = "general_curriculum"
    permission_mapping = GENERAL_EDUCATION_PERMISSIONS_MAPPING
    check_command_class = general_commands.VerifierCurriculumQuery
    complete_command_class = general_commands.CompleterCurriculumCommand
    schema = SpecificPersonRelatedSchema(training_type='GeneralEducation')
    serializer_mapping = {
        'PUT': serializers.GeneralEducationCompleterCurriculumCommandSerializer,
        'GET': serializers.CurriculumDetailsSerializer,
    }


class ContinuingCurriculumView(ContinuingEducationPersonRelatedMixin, CurriculumView):
    name = "continuing_curriculum"
    permission_mapping = CONTINUING_EDUCATION_PERMISSIONS_MAPPING
    complete_command_class = continuing_commands.CompleterCurriculumCommand
    schema = SpecificPersonRelatedSchema(training_type='ContinuingEducation')
    serializer_mapping = {
        'PUT': serializers.ContinuingEducationCompleterCurriculumCommandSerializer,
        'GET': serializers.CurriculumDetailsSerializer,
    }


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
            if self.request
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
        if self.request:
            context['candidate'] = self.candidate
        return context

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status(request.user.person)
        return response

    def _check_perms_update(self):
        if self.experience.valuated_from_trainings:
            raise PermissionDenied(_("This experience cannot be updated as it has already been valuated."))

    def update(self, request, *args, **kwargs):
        self._check_perms_update()
        response = super().update(request, *args, **kwargs)
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status(request.user.person)
        return response

    def destroy(self, request, *args, **kwargs):
        if self.experience.valuated_from_trainings:
            raise PermissionDenied(_("This experience cannot be updated as it has already been valuated."))

        response = super().destroy(request, *args, **kwargs)
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status(request.user.person)
        return response


class BaseProfessionalExperienceViewSet(ExperienceViewSet):
    model = ProfessionalExperience
    serializer_class = ProfessionalExperienceSerializer


class ProfessionalExperienceViewSet(PersonRelatedMixin, BaseProfessionalExperienceViewSet):
    name = "professional_experiences"
    permission_classes = [partial(IsSelfPersonTabOrTabPermission, permission_suffix="curriculum")]

    def get_object(self):
        return self.experience


class GeneralProfessionalExperienceViewSet(GeneralEducationPersonRelatedMixin, BaseProfessionalExperienceViewSet):
    name = "general_professional_experiences"
    permission_mapping = GENERAL_EDUCATION_PERMISSIONS_MAPPING

    def get_object(self):
        return self.experience


class ContinuingProfessionalExperienceViewSet(ContinuingEducationPersonRelatedMixin, BaseProfessionalExperienceViewSet):
    name = "continuing_professional_experiences"
    permission_mapping = CONTINUING_EDUCATION_PERMISSIONS_MAPPING

    def get_object(self):
        return self.experience


class BaseEducationalExperienceViewSet(ExperienceViewSet):
    model = EducationalExperience
    serializer_class = EducationalExperienceSerializer


class EducationalExperienceViewSet(PersonRelatedMixin, BaseEducationalExperienceViewSet):
    name = "educational_experiences"
    permission_classes = [partial(IsSelfPersonTabOrTabPermission, permission_suffix="curriculum")]

    def _check_perms_update(self):
        # With doctorate
        if any(
            training_type in AnneeInscriptionFormationTranslator.DOCTORATE_EDUCATION_TYPES
            for training_type in self.experience.valuated_from_trainings
        ):
            raise PermissionDenied(_("This experience cannot be updated as it has already been valuated."))

    def get_object(self):
        return self.experience


class GeneralEducationalExperienceViewSet(GeneralEducationPersonRelatedMixin, BaseEducationalExperienceViewSet):
    name = "general_educational_experiences"
    permission_mapping = GENERAL_EDUCATION_PERMISSIONS_MAPPING

    def _check_perms_update(self):
        if not all(
            training_type in AnneeInscriptionFormationTranslator.CONTINUING_EDUCATION_TYPES
            for training_type in self.experience.valuated_from_trainings
        ):
            raise PermissionDenied(_("This experience cannot be updated as it has already been valuated."))

    def get_object(self):
        return self.experience


class ContinuingEducationalExperienceViewSet(ContinuingEducationPersonRelatedMixin, BaseEducationalExperienceViewSet):
    name = "continuing_educational_experiences"
    permission_mapping = CONTINUING_EDUCATION_PERMISSIONS_MAPPING

    def get_object(self):
        return self.experience
