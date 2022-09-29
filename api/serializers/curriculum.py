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
from functools import partial

from rest_framework import serializers

from admission.api.serializers.fields import DoctorateAdmissionField
from admission.api.serializers.mixins import GetDefaultContextParam
from admission.ddd.projet_doctoral.preparation.domain.service.i_profil_candidat import IProfilCandidatTranslator
from base.api.serializers.academic_year import RelatedAcademicYearField
from base.models.academic_year import current_academic_year
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.models.organization import Organization
from base.models.person import Person
from osis_profile.models import (
    ProfessionalExperience,
    EducationalExperience,
    EducationalExperienceYear,
    BelgianHighSchoolDiploma,
    ForeignHighSchoolDiploma,
)
from reference.api.serializers.country import RelatedCountryField
from reference.api.serializers.language import RelatedLanguageField
from reference.models.diploma_title import DiplomaTitle


class ProfessionalExperienceSerializer(serializers.ModelSerializer):
    person = serializers.HiddenField(
        default=serializers.CreateOnlyDefault(GetDefaultContextParam('candidate')),
    )
    valuated_from = DoctorateAdmissionField(many=True)

    class Meta:
        model = ProfessionalExperience
        exclude = [
            'id',
        ]


class LiteProfessionalExperienceSerializer(ProfessionalExperienceSerializer):
    class Meta:
        model = ProfessionalExperience
        fields = [
            'uuid',
            'institute_name',
            'start_date',
            'end_date',
            'type',
            'valuated_from',
        ]


class EducationalExperienceYearSerializer(serializers.ModelSerializer):
    academic_year = RelatedAcademicYearField()

    class Meta:
        model = EducationalExperienceYear
        exclude = [
            'id',
            'educational_experience',
        ]


RelatedDiplomaField = partial(
    serializers.SlugRelatedField,
    slug_field='uuid',
    queryset=DiplomaTitle.objects.all(),
    allow_null=True,
)

RelatedInstitute = partial(
    serializers.SlugRelatedField,
    slug_field='uuid',
    queryset=Organization.objects.filter(establishment_type=EstablishmentTypeEnum.NON_UNIVERSITY_HIGHER.name),
    allow_null=True,
)


class EducationalExperienceSerializer(serializers.ModelSerializer):
    educationalexperienceyear_set = EducationalExperienceYearSerializer(many=True)
    country = RelatedCountryField()
    linguistic_regime = RelatedLanguageField(required=False)
    person = serializers.HiddenField(
        default=serializers.CreateOnlyDefault(GetDefaultContextParam('candidate')),
    )
    program = RelatedDiplomaField(required=False)
    valuated_from = DoctorateAdmissionField(many=True)
    institute = RelatedInstitute(required=False)

    YEAR_FIELDS_TO_UPDATE = [
        'registered_credit_number',
        'acquired_credit_number',
        'result',
        'transcript',
        'transcript_translation',
    ]

    class Meta:
        model = EducationalExperience
        depth = 1
        exclude = [
            'id',
        ]

    @classmethod
    def _set_study_system(cls, validated_data):
        institute = validated_data.get('institute')

        # If an institute with a teaching type is specified, the study system is based on it
        if institute and institute.teaching_type:
            validated_data['study_system'] = institute.teaching_type
        else:
            validated_data['study_system'] = ''

    def create(self, validated_data):
        experience_year_data = validated_data.pop('educationalexperienceyear_set')

        self._set_study_system(validated_data)
        educational_experience = super().create(validated_data)

        # Create the experience years related to the created experience
        for new_experience_year_data in experience_year_data:
            new_experience_year = EducationalExperienceYear(
                educational_experience=educational_experience,
                **new_experience_year_data,
            )
            new_experience_year.save()

        return educational_experience

    def update(self, instance, validated_data):
        experience_year_data = {
            experience_year.get('academic_year').pk: experience_year
            for experience_year in validated_data.pop('educationalexperienceyear_set')
        }

        self._set_study_system(validated_data)
        educational_experience: EducationalExperience = super().update(instance, validated_data)

        # Loop over the existing experience years to update / delete them if necessary
        for experience_year in educational_experience.educationalexperienceyear_set.all():
            current_experience_year_data = experience_year_data.pop(experience_year.academic_year.pk, None)

            if current_experience_year_data:
                # Update it
                for field in self.YEAR_FIELDS_TO_UPDATE:
                    setattr(experience_year, field, current_experience_year_data[field])

                experience_year.save(update_fields=self.YEAR_FIELDS_TO_UPDATE)

            else:
                # Delete it
                experience_year.delete()

        for academic_year in experience_year_data:
            # Save the new experience years
            new_experience_year = EducationalExperienceYear(
                educational_experience=educational_experience,
                **experience_year_data[academic_year],
            )
            new_experience_year.save()

        return educational_experience


class LiteEducationalExperienceYearSerializer(EducationalExperienceYearSerializer):
    class Meta:
        model = EducationalExperienceYear
        fields = [
            'academic_year',
        ]


class LiteEducationalExperienceSerializer(EducationalExperienceSerializer):
    educationalexperienceyear_set = LiteEducationalExperienceYearSerializer(many=True)

    class Meta:
        model = EducationalExperience
        fields = [
            'uuid',
            'institute_name',
            'institute',
            'program',
            'education_name',
            'educationalexperienceyear_set',
            'valuated_from',
        ]


class CurriculumFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = [
            'curriculum',
        ]


class CurriculumSerializer(serializers.Serializer):
    professional_experiences = LiteProfessionalExperienceSerializer(many=True)
    educational_experiences = LiteEducationalExperienceSerializer(many=True)
    file = CurriculumFileSerializer()
    minimal_year = serializers.SerializerMethodField()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Define a custom schema as the default schema type of a SerializerMethodField is string
        self.fields['minimal_year'].field_schema = {'type': 'integer'}

    def get_minimal_year(self, _):
        related_person = self.context.get('related_person')
        belgian_diploma = (
            BelgianHighSchoolDiploma.objects.filter(person=related_person)
            .select_related('academic_graduation_year')
            .first()
        )
        foreign_diploma = (
            ForeignHighSchoolDiploma.objects.filter(person=related_person)
            .select_related('academic_graduation_year')
            .first()
        )
        current_year = current_academic_year()
        min_year = 1 + max(
            year
            for year in [
                belgian_diploma.academic_graduation_year.year if belgian_diploma else None,
                foreign_diploma.academic_graduation_year.year if foreign_diploma else None,
                related_person.last_registration_year.year if related_person.last_registration_year else None,
                current_year.year - IProfilCandidatTranslator.NB_MAX_ANNEES_CV_REQUISES,
            ]
            if year
        )

        return min_year
