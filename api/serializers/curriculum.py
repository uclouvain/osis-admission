# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework import serializers

from base.api.serializers.academic_year import RelatedAcademicYearField
from base.models.academic_year import AcademicYear
from osis_profile.models import Experience, CurriculumYear


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = (
            "validated_from",
            "course_type",
            "is_valuated",
        )


class CurriculumYearSerializer(serializers.ModelSerializer):
    academic_graduation_year = RelatedAcademicYearField()
    experiences = ExperienceSerializer(many=True)

    class Meta:
        model = CurriculumYear
        fields = (
            "academic_graduation_year",
            "experiences",
        )


class CurriculumSerializer(serializers.Serializer):
    curriculum_years = CurriculumYearSerializer(many=True)

    @staticmethod
    def load_curriculum(instance):
        instance.curriculum_years = CurriculumYear.objects.filter(person=instance)

    def to_representation(self, instance):
        self.load_curriculum(instance)
        return super().to_representation(instance)

    @staticmethod
    def update_curriculum_year(person, curriculum_year_data):
        academic_year = AcademicYear.objects.get(year=curriculum_year_data.get("academic_graduation_year").year)
        return CurriculumYear.objects.update_or_create(person=person, academic_graduation_year=academic_year)

    @staticmethod
    def add_experience(curriculum_year, experience_data):
        Experience.objects.create(curriculum_year=curriculum_year, **experience_data)

    def update(self, instance, validated_data):
        person = instance
        for curriculum_year_data in validated_data.get("curriculum_years"):
            curriculum_year, _ = self.update_curriculum_year(person, curriculum_year_data)
            experiences_data = curriculum_year_data.get("experiences")
            if experiences_data:
                # first remove all previous not valuated experiences
                curriculum_year.experiences.filter(validated=False).delete()
                # then add the receive ones
                for experience_data in experiences_data:
                    self.add_experience(curriculum_year, experience_data)
        self.load_curriculum(instance)
        return person
