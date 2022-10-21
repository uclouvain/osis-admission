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
from admission.contrib.models import AdmissionFormItemInstantiation

from admission.utils import (
    get_cached_admission_perm_obj,
    get_cached_continuing_education_admission_perm_obj,
    get_cached_general_education_admission_perm_obj,
)
from base.models.person import Person
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

    def get_queryset(self):
        admission = self.get_permission_object()

        candidate = Person.objects.select_related(
            'country_of_citizenship',
            'belgianhighschooldiploma',
            'foreignhighschooldiploma__linguistic_regime',
        ).get(pk=admission.candidate_id)

        return AdmissionFormItemInstantiation.objects.form_items_by_admission(
            admission=admission,
            tabs=[self.kwargs.get('tab')],
            candidate=candidate,
        ).order_by('display_according_education', 'weight')


class GeneralSpecificQuestionListView(SpecificQuestionListView):
    name = "general-specific-questions"
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission',
    }
    schema = SpecificQuestionListSchema(operation_id_base='_general_specific_question')

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])


class ContinuingSpecificQuestionListView(SpecificQuestionListView):
    name = "continuing-specific-questions"
    schema = SpecificQuestionListSchema(operation_id_base='_continuing_specific_question')
    permission_mapping = {
        'GET': 'admission.view_continuingeducationadmission',
    }

    def get_permission_object(self):
        return get_cached_continuing_education_admission_perm_obj(self.kwargs['uuid'])


class DoctorateSpecificQuestionListView(SpecificQuestionListView):
    name = "doctorate-specific-questions"
    schema = SpecificQuestionListSchema(operation_id_base='_doctorate_specific_question')
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])
