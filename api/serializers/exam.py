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
from django.utils.functional import cached_property
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from admission.infrastructure.admission.domain.service.profil_candidat import ProfilCandidatTranslator
from base.api.serializers.academic_year import RelatedAcademicYearField
from osis_profile.models import Exam, EducationGroupYearExam
from osis_profile.models.enums.exam import ExamTypes


class ExamSerializer(serializers.ModelSerializer):
    required = serializers.SerializerMethodField()
    title_fr = serializers.SerializerMethodField()
    title_en = serializers.SerializerMethodField()
    help_text_fr = serializers.SerializerMethodField()
    help_text_en = serializers.SerializerMethodField()
    is_valuated = serializers.SerializerMethodField()

    year = RelatedAcademicYearField(required=False)

    class Meta:
        model = Exam
        fields = (
            "required",
            "title_fr",
            "title_en",
            "help_text_fr",
            "help_text_en",
            "certificate",
            "year",
            "is_valuated",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['required'].field_schema = {'type': 'boolean'}
        self.fields['title_fr'].field_schema = {'type': 'string'}
        self.fields['title_en'].field_schema = {'type': 'string'}
        self.fields['help_text_fr'].field_schema = {'type': 'string'}
        self.fields['help_text_en'].field_schema = {'type': 'string'}
        self.fields['is_valuated'].field_schema = {'type': 'boolean'}

    @extend_schema_field(OpenApiTypes.STR)
    def get_title_fr(self, exam):
        return getattr(self.education_group_year_exam, 'title_fr', '')

    @extend_schema_field(OpenApiTypes.STR)
    def get_title_en(self, exam):
        return getattr(self.education_group_year_exam, 'title_en', '')

    @extend_schema_field(OpenApiTypes.STR)
    def get_help_text_fr(self, exam):
        return getattr(self.education_group_year_exam, 'help_text_fr', '')

    @extend_schema_field(OpenApiTypes.STR)
    def get_help_text_en(self, exam):
        return getattr(self.education_group_year_exam, 'help_text_en', '')

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_valuated(self, exam):
        return ProfilCandidatTranslator.examen_est_valorise(
            matricule=self.context['admission'].candidate.global_id,
            formation_sigle=self.context['admission'].training.acronym,
            formation_annee=self.context['admission'].training.academic_year.year,
        )

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_required(self, exam):
        return self.education_group_year_exam is not None

    @cached_property
    def education_group_year_exam(self):
        try:
            return EducationGroupYearExam.objects.get(education_group_year=self.context['admission'].training)
        except EducationGroupYearExam.DoesNotExist:
            return None

    def update(self, instance, validated_data):
        if self.education_group_year_exam is None:
            return instance
        Exam.objects.update_or_create(
            person=self.context['admission'].candidate,
            type=ExamTypes.FORMATION.name,
            education_group_year_exam=self.education_group_year_exam,
            defaults={
                "certificate": validated_data.get("certificate", None),
                "year": validated_data.get("year", None),
            },
        )
        return instance
