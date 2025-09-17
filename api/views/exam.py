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

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView

from admission.api import serializers
from admission.api.views.mixins import GeneralEducationPersonRelatedMixin
from osis_profile.models import Exam
from osis_profile.models.exam import ExamType
from osis_role.contrib.views import APIPermissionRequiredMixin


class BaseExamViewSet(
    APIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.ExamSerializer

    def get_object(self):
        admission = self.get_permission_object()
        try:
            return Exam.objects.get(
                person=admission.candidate,
                type__education_group_years=admission.training,
            )
        except Exam.DoesNotExist:
            return Exam()

    def get_serializer_context(self):
        serializer_context = super().get_serializer_context()
        # Avoid error during generateschema command
        if 'uuid' in self.kwargs:
            serializer_context['admission'] = self.get_permission_object()
        return serializer_context

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        admission = self.get_permission_object()
        if not ExamType.objects.filter(education_group_years=admission.training).exists():
            raise PermissionDenied(_("There is no required exam for this training."))
        response = self.update(request, *args, **kwargs)
        current_admission = self.get_permission_object()
        if current_admission:
            current_admission.update_detailed_status(request.user.person)
        return response


@extend_schema_view(
    get=extend_schema(operation_id='retrieve_exam_general_education_admission', tags=['person']),
    put=extend_schema(operation_id='update_exam_general_education_admission', tags=['person']),
)
class GeneralExamView(GeneralEducationPersonRelatedMixin, BaseExamViewSet):
    name = "general_exam"
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission_exam',
        'PUT': 'admission.change_generaleducationadmission_exam',
    }

    def get_object(self):
        return BaseExamViewSet.get_object(self)
