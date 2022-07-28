# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from rest_framework import generics

from admission.api import serializers
from admission.api.schema import ResponseSpecificSchema
from admission.api.serializers import SpecificQuestionSerializer
from admission.contrib.models import AdmissionFormItem

from admission.utils import get_cached_admission_perm_obj
from osis_role.contrib.views import APIPermissionRequiredMixin


class SpecificQuestionListSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.SpecificQuestionSerializer,
    }


class SpecificQuestionListView(APIPermissionRequiredMixin, generics.ListAPIView):
    name = "specific-questions"
    schema = SpecificQuestionListSchema()
    serializer_class = SpecificQuestionSerializer
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission_project',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get_queryset(self):
        return AdmissionFormItem.objects.filter(education=self.get_permission_object().doctorate).exclude(deleted=True)
