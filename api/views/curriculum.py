# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from functools import partial
from typing import Union

from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404, RetrieveAPIView
from rest_framework.mixins import UpdateModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from admission.api import serializers
from admission.api.permissions import IsSelfPersonTabOrTabPermission
from admission.api.serializers import ProfessionalExperienceSerializer
from admission.api.serializers.curriculum import EducationalExperienceSerializer
from admission.api.views.mixins import PersonRelatedMixin, PersonRelatedSchema
from osis_profile.models import ProfessionalExperience, EducationalExperience
from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    "CurriculumView",
    "ProfessionalExperienceViewSetSchema",
    "EducationalExperienceViewSetSchema",
    "ExperienceViewSet",
    "ProfessionalExperienceViewSet",
    "EducationalExperienceViewSet",
    "CurriculumFileView",
]


class CurriculumView(PersonRelatedMixin, APIPermissionRequiredMixin, RetrieveAPIView):
    permission_classes = [
        partial(IsSelfPersonTabOrTabPermission, permission_suffix="curriculum"),
    ]
    serializer_class = serializers.CurriculumSerializer
    name = "curriculum"
    pagination_class = None
    filter_backends = []

    def get(self, request, *args, **kwargs):
        """Return the experiences and the curriculum pdf of a person and the mandatory years to complete."""
        current_person = self.get_object()
        professional_experiences = ProfessionalExperience.objects.filter(person=current_person).prefetch_related(
            'valuated_from'
        )
        educational_experiences = EducationalExperience.objects.filter(person=current_person).prefetch_related(
            'valuated_from'
        )

        serializer = serializers.CurriculumSerializer(
            instance={
                'professional_experiences': professional_experiences,
                'educational_experiences': educational_experiences,
                'file': current_person,
            },
            context={
                'related_person': current_person,
            },
        )

        return Response(serializer.data)


class ProfessionalExperienceViewSetSchema(PersonRelatedSchema):
    operation_id_base = '_professional_experience'


class EducationalExperienceViewSetSchema(PersonRelatedSchema):
    operation_id_base = '_educational_experience'


class ExperienceViewSet(
    PersonRelatedMixin,
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

    permission_classes = [
        partial(IsSelfPersonTabOrTabPermission, permission_suffix="curriculum"),
    ]
    pagination_class = None
    filter_backends = []
    model = None

    def get_queryset(self):
        return (
            self.model.objects.filter(person=self.candidate).prefetch_related('valuated_from')
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
            self.get_permission_object().update_detailed_status()
        return response

    def update(self, request, *args, **kwargs):
        if self.experience.valuated_from.exists():
            raise PermissionDenied(_("This experience cannot be updated as it has already been valuated."))

        response = super().update(request, *args, **kwargs)
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status()
        return response

    def destroy(self, request, *args, **kwargs):
        if self.experience.valuated_from.exists():
            raise PermissionDenied(_("This experience cannot be updated as it has already been valuated."))

        response = super().destroy(request, *args, **kwargs)
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status()
        return response


class ProfessionalExperienceViewSet(ExperienceViewSet):
    schema = ProfessionalExperienceViewSetSchema()
    name = "professional_experiences"
    model = ProfessionalExperience
    serializer_class = ProfessionalExperienceSerializer


class EducationalExperienceViewSet(ExperienceViewSet):
    schema = EducationalExperienceViewSetSchema()
    name = "educational_experiences"
    model = EducationalExperience
    serializer_class = EducationalExperienceSerializer


class CurriculumFileView(PersonRelatedMixin, APIPermissionRequiredMixin, UpdateModelMixin, RetrieveAPIView):
    name = "curriculum_file"
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.CurriculumFileSerializer
    permission_classes = [
        partial(IsSelfPersonTabOrTabPermission, permission_suffix="curriculum"),
    ]

    def put(self, request, *args, **kwargs):
        response = self.update(request, *args, **kwargs)
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status()
        return response
