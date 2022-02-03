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
from django.conf import settings
from django.utils.translation import gettext as _, get_language

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from base.api.serializers.academic_year import RelatedAcademicYearField
from base.models.education_group_year import EducationGroupYear
from base.models.organization import Organization
from base.models.person import Person
from osis_profile.models import Experience, CurriculumYear
from reference.api.serializers.country import RelatedCountryField
from reference.api.serializers.language import RelatedLanguageField
from reference.models.language import Language
from reference.models.country import Country


# Nested serializers
class CurriculumYearSerializer(serializers.ModelSerializer):
    academic_year = RelatedAcademicYearField()

    class Meta:
        model = CurriculumYear
        fields = (
            'academic_year',
            'id',
        )


class EducationGroupYearSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = EducationGroupYear
        fields = (
            'title',
            'uuid',
        )

    @staticmethod
    def get_title(obj):
        return obj.title if get_language() == settings.LANGUAGE_CODE else obj.title_english


class CountrySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = (
            'iso_code',
            'name',
        )

    @staticmethod
    def get_name(obj):
        return obj.name if get_language() == settings.LANGUAGE_CODE else obj.name_en


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = (
            'acronym',
            'name',
            'uuid',
        )


class LanguageSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Language
        fields = (
            'code',
            'name',
        )

    @staticmethod
    def get_name(obj):
        return obj.name if get_language() == settings.LANGUAGE_CODE else obj.name_en


# Experience serializers
class ExperienceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Experience
        fields = '__all__'
        extra_kwargs = {
            "curriculum_year": {
                "required": False,
            },
        }


class ExperienceOutputSerializer(ExperienceSerializer):
    curriculum_year = CurriculumYearSerializer()
    country = CountrySerializer()
    program = EducationGroupYearSerializer(allow_null=True)
    linguistic_regime = LanguageSerializer(allow_null=True)
    institute = OrganizationSerializer(allow_null=True)
    is_valuated = serializers.SerializerMethodField()

    @classmethod
    def get_is_valuated(cls, experience):
        return experience.doctorateadmission_set.exists()


class ExperienceInputSerializer(ExperienceSerializer):
    academic_year = RelatedAcademicYearField(required=False)
    country = RelatedCountryField()
    linguistic_regime = RelatedLanguageField(required=False)

    def __init__(self, related_person=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.related_person = related_person

    def validate(self, data):
        # The related year must be specified
        if not data.get('academic_year') and not data.get('curriculum_year'):
            raise ValidationError(_("Please specify the experience's year."))

        return super().validate(data)

    def _get_or_create_curriculum_year_from_academic_year(self, validated_data):
        if not validated_data.get('curriculum_year'):
            # Get (and eventually create) the curriculum year related to the specified academic_year
            validated_data['curriculum_year'] = CurriculumYear.objects.get_or_create(
                person=self.related_person,
                academic_year=validated_data.pop('academic_year'),
            )[0]

    def create(self, validated_data):
        self._get_or_create_curriculum_year_from_academic_year(validated_data=validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._get_or_create_curriculum_year_from_academic_year(validated_data=validated_data)
        return super().update(instance, validated_data)


class CurriculumFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = [
            'curriculum',
        ]
