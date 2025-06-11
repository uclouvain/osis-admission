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
from functools import partial

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins
from rest_framework.generics import GenericAPIView

from admission.api import serializers
from admission.api.permissions import IsSelfPersonTabOrTabPermission
from admission.api.views.mixins import (
    ContinuingEducationPersonRelatedMixin,
    GeneralEducationPersonRelatedMixin,
    PersonRelatedMixin,
)
from osis_role.contrib.views import APIPermissionRequiredMixin


class BaseSecondaryStudiesViewSet(
    APIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.HighSchoolDiplomaSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        response = self.update(request, *args, **kwargs)
        current_admission = self.get_permission_object()
        if current_admission:
            current_admission.specific_question_answers = request.data.get('specific_question_answers')
            current_admission.save(update_fields=['specific_question_answers'])
            current_admission.update_detailed_status(request.user.person)
        return response


@extend_schema_view(
    get=extend_schema(operation_id="retrieveHighSchoolDiploma", tags=['person']),
    put=extend_schema(operation_id="updateHighSchoolDiploma", tags=['person']),
)
class CommonSecondaryStudiesViewSet(PersonRelatedMixin, BaseSecondaryStudiesViewSet):
    name = "secondary-studies"
    permission_classes = [partial(IsSelfPersonTabOrTabPermission, permission_suffix='secondary_studies')]


@extend_schema_view(
    get=extend_schema(operation_id="retrieveHighSchoolDiplomaAdmission", tags=['person']),
    put=extend_schema(operation_id="updateHighSchoolDiplomaAdmission", tags=['person']),
)
class SecondaryStudiesViewSet(PersonRelatedMixin, BaseSecondaryStudiesViewSet):
    name = "doctorate-secondary-studies"
    permission_classes = [partial(IsSelfPersonTabOrTabPermission, permission_suffix='secondary_studies')]


@extend_schema_view(
    get=extend_schema(operation_id="retrieveHighSchoolDiplomaGeneralEducationAdmission", tags=['person']),
    put=extend_schema(operation_id="updateHighSchoolDiplomaGeneralEducationAdmission", tags=['person']),
)
class GeneralSecondaryStudiesView(GeneralEducationPersonRelatedMixin, BaseSecondaryStudiesViewSet):
    name = "general_secondary_studies"
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission_secondary_studies',
        'PUT': 'admission.change_generaleducationadmission_secondary_studies',
    }

    def get_serializer_context(self):
        serializer_context = super().get_serializer_context()
        if self.request:
            serializer_context['training_type'] = self.get_permission_object().training.education_group_type.name
        return serializer_context


@extend_schema_view(
    get=extend_schema(operation_id="retrieveHighSchoolDiplomaContinuingEducationAdmission", tags=['person']),
    put=extend_schema(operation_id="updateHighSchoolDiplomaContinuingEducationAdmission", tags=['person']),
)
class ContinuingSecondaryStudiesView(ContinuingEducationPersonRelatedMixin, BaseSecondaryStudiesViewSet):
    name = "continuing_secondary_studies"
    permission_mapping = {
        'GET': 'admission.view_continuingeducationadmission_secondary_studies',
        'PUT': 'admission.change_continuingeducationadmission_secondary_studies',
    }
