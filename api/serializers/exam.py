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
from rest_framework import serializers

from admission.infrastructure.admission.domain.service.profil_candidat import ProfilCandidatTranslator
from base.api.serializers.academic_year import RelatedAcademicYearField
from osis_profile.models import Exam, EducationGroupYearExam
from osis_profile.models.enums.exam import ExamTypes


class ExamSerializer(serializers.ModelSerializer):
    title_fr = serializers.CharField(source="education_group_year_exam.title_fr", read_only=True)
    title_en = serializers.CharField(source="education_group_year_exam.title_en", read_only=True)
    help_text_fr = serializers.CharField(source="education_group_year_exam.help_text_fr", read_only=True)
    help_text_en = serializers.CharField(source="education_group_year_exam.help_text_en", read_only=True)
    is_valuated = serializers.SerializerMethodField()

    year = RelatedAcademicYearField(required=False)

    class Meta:
        model = Exam
        fields = (
            "title_fr",
            "title_en",
            "help_text_fr",
            "help_text_en",
            "certificate",
            "year",
            "is_valuated",
        )

    def get_is_valuated(self, exam):
        return self.valuation.est_valorise

    @cached_property
    def valuation(self):
        return ProfilCandidatTranslator.valorisation_etudes_secondaires(matricule=self.context['admission'].candidate.global_id)

    def update(self, instance, validated_data):
        try:
            education_group_year_exam = EducationGroupYearExam.objects.get(education_group_year=self.context['admission'].training)
        except EducationGroupYearExam.DoesNotExist:
            return instance
        Exam.objects.update_or_create(
            person=self.context['admission'].candidate,
            type=ExamTypes.FORMATION.name,
            education_group_year_exam=education_group_year_exam,
            defaults={
                "certificate": validated_data.get("certificate", None),
                "year": validated_data.get("year", None),
            },
        )
        return instance
