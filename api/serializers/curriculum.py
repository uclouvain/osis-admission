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
from rest_framework.exceptions import ValidationError

from base.api.serializers.academic_year import RelatedAcademicYearField
from base.models.academic_year import AcademicYear
from osis_profile.models import Experience, CurriculumYear


class ExperienceSerializer(serializers.ModelSerializer):
    valuated_from = serializers.UUIDField(source="valuated_from.uuid", read_only=True)

    class Meta:
        model = Experience
        fields = '__all__'
        extra_kwargs = {
            "curriculum_year": {
                "required": False,
            },
        }


class ExperienceUpdatingSerializer(ExperienceSerializer):

    def get_extra_kwargs(self):
        extra_kwargs = super().get_extra_kwargs()
        extra_kwargs["curriculum_year"]["read_only"] = True
        return extra_kwargs


class ExperienceCreationSerializer(ExperienceSerializer):
    academic_graduation_year = RelatedAcademicYearField(required=False)

    def __init__(self, related_person=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.related_person = related_person

    def validate(self, data):
        # The related year must be specified
        if not data.get('academic_graduation_year') and not data.get('curriculum_year'):
            raise ValidationError("Please specify the experience's year")

        return super().validate(data)

    def create(self, validated_data):
        if not validated_data.get('curriculum_year'):
            # Get (and eventually create) the curriculum year related to the specified academic_year
            validated_data['curriculum_year'] = CurriculumYear.objects.get_or_create(
                person=self.related_person,
                academic_graduation_year=validated_data.pop('academic_graduation_year'),
            )[0]

        return super().create(validated_data)
