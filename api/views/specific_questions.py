# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.response import Response

from admission.api import serializers
from admission.api.serializers import SpecificQuestionSerializer
from admission.ddd.admission.formation_continue.commands import (
    CompleterQuestionsSpecifiquesCommand as CompleterQuestionsSpecifiquesFormationContinueCommand,
)
from admission.ddd.admission.formation_generale.commands import (
    CompleterQuestionsSpecifiquesCommand as CompleterQuestionsSpecifiquesFormationGeneraleCommand,
)
from admission.infrastructure.admission.domain.service.profil_candidat import (
    ProfilCandidatTranslator,
)
from admission.models import AdmissionFormItemInstantiation
from admission.utils import (
    get_cached_admission_perm_obj,
    get_cached_continuing_education_admission_perm_obj,
    get_cached_general_education_admission_perm_obj,
)
from base.models.person import Person
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin


class SpecificQuestionListView(APIPermissionRequiredMixin, generics.ListAPIView):
    name = "specific-questions"
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


@extend_schema_view(
    get=extend_schema(
        responses=serializers.SpecificQuestionSerializer,
        operation_id='list_general_specific_questions',
    ),
)
class GeneralSpecificQuestionListView(SpecificQuestionListView):
    name = "general-specific-questions"
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission',
    }

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])


@extend_schema_view(
    get=extend_schema(
        responses=serializers.SpecificQuestionSerializer,
        operation_id='list_continuing_specific_questions',
    ),
)
class ContinuingSpecificQuestionListView(SpecificQuestionListView):
    name = "continuing-specific-questions"
    permission_mapping = {
        'GET': 'admission.view_continuingeducationadmission',
    }

    def get_permission_object(self):
        return get_cached_continuing_education_admission_perm_obj(self.kwargs['uuid'])


@extend_schema_view(
    get=extend_schema(
        responses=serializers.SpecificQuestionSerializer,
        operation_id='list_doctorate_specific_questions',
    ),
)
class DoctorateSpecificQuestionListView(SpecificQuestionListView):
    name = "doctorate-specific-questions"
    permission_mapping = {
        'GET': 'admission.api_view_doctorateadmission',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])


class GeneralSpecificQuestionAPIView(APIPermissionRequiredMixin, GenericAPIView):
    name = 'general_specific_question'
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission_specific_question',
        'PUT': 'admission.change_generaleducationadmission_specific_question',
    }
    filter_backends = []
    pagination_class = None

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])

    @extend_schema(
        request=serializers.ModifierQuestionsSpecifiquesFormationGeneraleCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='update_general_specific_question',
    )
    def put(self, request, *args, **kwargs):
        serializer = serializers.ModifierQuestionsSpecifiquesFormationGeneraleCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(
            CompleterQuestionsSpecifiquesFormationGeneraleCommand(
                uuid_proposition=self.kwargs['uuid'],
                **serializer.data,
            )
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GeneralIdentificationView(APIPermissionRequiredMixin, RetrieveAPIView):
    name = "general_identification"
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission_specific_question',
    }
    filter_backends = []
    pagination_class = None

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])

    @extend_schema(
        responses=serializers.IdentificationDTOSerializer,
        operation_id='retrieve_general_identification',
    )
    def get(self, request, *args, **kwargs):
        admission = self.get_permission_object()
        identification_dto = ProfilCandidatTranslator.get_identification(
            matricule=admission.candidate.global_id,
        )
        serializer = serializers.IdentificationDTOSerializer(instance=identification_dto)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ContinuingSpecificQuestionAPIView(APIPermissionRequiredMixin, GenericAPIView):
    name = 'continuing_specific_question'
    permission_mapping = {
        'GET': 'admission.view_continuingeducationadmission_specific_question',
        'PUT': 'admission.change_continuingeducationadmission_specific_question',
    }
    filter_backends = []
    pagination_class = None

    def get_permission_object(self):
        return get_cached_continuing_education_admission_perm_obj(self.kwargs['uuid'])

    @extend_schema(
        request=serializers.ModifierQuestionsSpecifiquesFormationContinueCommandSerializer,
        responses=serializers.PropositionIdentityDTOSerializer,
        operation_id='update_continuing_specific_question',
    )
    def put(self, request, *args, **kwargs):
        serializer = serializers.ModifierQuestionsSpecifiquesFormationContinueCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(
            CompleterQuestionsSpecifiquesFormationContinueCommand(
                uuid_proposition=self.kwargs['uuid'],
                **serializer.data,
            )
        )
        admission = self.get_permission_object()
        admission.update_detailed_status(request.user.person)
        serializer = serializers.PropositionIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)
