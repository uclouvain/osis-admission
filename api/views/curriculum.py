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
from typing import Optional

from django.db.models import Exists, OuterRef
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404, RetrieveAPIView
from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView

from admission.api import serializers
from admission.api.permissions import IsSelfPersonTabOrTabPermission
from admission.api.schema import ResponseSpecificSchema
from admission.api.views.mixins import PersonRelatedMixin, PersonRelatedSchema
from admission.contrib.models import DoctorateAdmission
from osis_profile.models import Experience
from osis_role.contrib.views import APIPermissionRequiredMixin


class CurriculumExperienceSchema(ResponseSpecificSchema, PersonRelatedSchema):
    operation_id_base = "_curriculum_experience"

    serializer_mapping = {
        "GET": serializers.ExperienceOutputSerializer,
        "PUT": (
            serializers.ExperienceInputSerializer,
            serializers.ExperienceOutputSerializer,
        ),
        "POST": (
            serializers.ExperienceInputSerializer,
            serializers.ExperienceOutputSerializer,
        ),
        "DELETE": (),
    }


class CurriculumExperienceView(PersonRelatedMixin, APIPermissionRequiredMixin, APIView):
    schema = CurriculumExperienceSchema()
    permission_classes = [
        partial(IsSelfPersonTabOrTabPermission, permission_suffix="curriculum"),
    ]
    name = "curriculum"

    def get_queryset(self):
        """Return the list of experiences of the person."""
        return (
            Experience.objects.filter(curriculum_year__person=self.get_object())
            .annotate(
                is_valuated=Exists(
                    DoctorateAdmission.valuated_experiences.through.objects.filter(
                        experience_id=OuterRef("pk"),
                    )
                )
            )
            .order_by("curriculum_year__academic__year")
        )

    def get_experience(self) -> Optional[Experience]:
        """Get the current experience from its uuid."""
        return get_object_or_404(self.get_queryset(), uuid=self.kwargs.get("xp"))


class CurriculumExperienceListAndCreateView(CurriculumExperienceView):
    def get(self, request, *args, **kwargs):
        """Return the list of experiences from the person's CV."""
        serializer = serializers.ExperienceOutputSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Add an experience to the person's CV."""
        serializer = serializers.ExperienceInputSerializer(data=request.data, related_person=self.get_object())
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status()

        output_data = serializers.ExperienceOutputSerializer(serializer.instance).data
        return Response(output_data, status=status.HTTP_201_CREATED)


class CurriculumExperienceDetailUpdateAndDeleteView(CurriculumExperienceView):
    def get(self, request, *args, **kwargs):
        """Return a specific experience from the person's CV."""
        serializer = serializers.ExperienceOutputSerializer(self.get_experience())
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """Update one of the experiences from the person's CV."""
        experience_to_update = self.get_experience()

        if experience_to_update.is_valuated:
            raise PermissionDenied(_("This experience cannot be updated as it has already been valuated."))

        serializer = serializers.ExperienceInputSerializer(
            instance=experience_to_update,
            data=request.data,
            related_person=self.get_object(),
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        output_data = serializers.ExperienceOutputSerializer(serializer.instance).data
        return Response(output_data)

    def delete(self, request, *args, **kwargs):
        """Remove one of the experiences from the person's CV."""
        experience_to_delete = self.get_experience()

        if experience_to_delete.is_valuated:
            raise PermissionDenied(_("This experience cannot be deleted as it has already been valuated."))

        experience_to_delete.delete()
        if self.get_permission_object():
            self.get_permission_object().update_detailed_status()

        return Response(status=status.HTTP_204_NO_CONTENT)


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
