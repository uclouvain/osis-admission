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
from django.conf import settings
from django.db import transaction
from django.utils import translation
from django.utils.functional import cached_property
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from admission.infrastructure.admission.shared_kernel.domain.service.profil_candidat import (
    ProfilCandidatTranslator,
)
from admission.models.exam import AdmissionExam
from base.api.serializers.academic_year import RelatedAcademicYearField
from osis_profile.models import Exam
from osis_profile.models.exam import ExamType


class ExamSerializer(serializers.ModelSerializer):
    required = serializers.SerializerMethodField()
    title_fr = serializers.SerializerMethodField()
    title_en = serializers.SerializerMethodField()
    is_valuated = serializers.SerializerMethodField()

    year = RelatedAcademicYearField(required=False)

    class Meta:
        model = Exam
        fields = (
            "required",
            "title_fr",
            "title_en",
            "certificate",
            "year",
            "is_valuated",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['required'].field_schema = {'type': 'boolean'}
        self.fields['title_fr'].field_schema = {'type': 'string'}
        self.fields['title_en'].field_schema = {'type': 'string'}
        self.fields['is_valuated'].field_schema = {'type': 'boolean'}

    @extend_schema_field(OpenApiTypes.STR)
    def get_title_fr(self, exam):
        with translation.override(settings.LANGUAGE_CODE_FR):
            return getattr(self.exam_type, 'title', '')

    @extend_schema_field(OpenApiTypes.STR)
    def get_title_en(self, exam):
        with translation.override(settings.LANGUAGE_CODE_EN):
            return getattr(self.exam_type, 'title', '')

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_valuated(self, exam):
        return ProfilCandidatTranslator.examen_est_valorise(exam.uuid)

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_required(self, exam):
        return self.exam_type is not None

    @cached_property
    def exam_type(self):
        try:
            return ExamType.objects.get(education_group_years=self.context['admission'].training)
        except ExamType.DoesNotExist:
            return None

    @transaction.atomic
    def update(self, instance, validated_data):
        if self.exam_type is None:
            return instance
        try:
            exam = AdmissionExam.objects.select_related('exam').get(admission=self.context['admission'])
            exam.certificate = validated_data.get("certificate", None)
            exam.year = validated_data.get("year", None)
            exam.save()
        except AdmissionExam.DoesNotExist:
            exam = Exam.objects.create(
                person=self.context['admission'].candidate,
                type=self.exam_type,
                certificate=validated_data.get("certificate", None),
                year=validated_data.get("year", None),
            )
            AdmissionExam.objects.create(admission=self.context['admission'], exam=exam)
        return instance
