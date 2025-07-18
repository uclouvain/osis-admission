# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

from functools import partial

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from admission.api.serializers.fields import AnswerToSpecificQuestionField
from admission.api.serializers.mixins import GetDefaultContextParam
from admission.ddd.admission.doctorat.preparation import commands as doctorate_commands
from admission.ddd.admission.formation_continue import commands as continuing_commands
from admission.ddd.admission.formation_generale import commands as general_commands
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from admission.infrastructure.admission.domain.service.profil_candidat import (
    ProfilCandidatTranslator,
)
from base.api.serializers.academic_year import RelatedAcademicYearField
from base.models.academic_year import current_academic_year
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.models.organization import Organization
from base.utils.serializers import DTOSerializer
from osis_profile.models import (
    EducationalExperience,
    EducationalExperienceYear,
    ProfessionalExperience,
)
from reference.api.serializers.country import RelatedCountryField
from reference.api.serializers.language import RelatedLanguageField
from reference.models.diploma_title import DiplomaTitle


class ProfessionalExperienceSerializer(serializers.ModelSerializer):
    person = serializers.HiddenField(
        default=serializers.CreateOnlyDefault(GetDefaultContextParam('candidate')),
    )
    valuated_from_trainings = serializers.SerializerMethodField()

    class Meta:
        model = ProfessionalExperience
        exclude = [
            'id',
        ]
        read_only_fields = ['external_id']

    @staticmethod
    @extend_schema_field(serializers.ListSerializer(child=serializers.CharField()))
    def get_valuated_from_trainings(value):
        return [
            AnneeInscriptionFormationTranslator.ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE.get(training_type)
            for training_type in getattr(value, 'valuated_from_trainings', [])
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
            'certificate',
            'valuated_from_trainings',
            'external_id',
        ]
        read_only_fields = ['external_id']


class EducationalExperienceYearSerializer(serializers.ModelSerializer):
    academic_year = RelatedAcademicYearField()

    class Meta:
        model = EducationalExperienceYear
        exclude = [
            'id',
            'educational_experience',
            'external_id',
            'reduction',
            'is_102_change_of_course',
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
    queryset=Organization.objects.filter(
        establishment_type__in=[
            EstablishmentTypeEnum.NON_UNIVERSITY_HIGHER.name,
            EstablishmentTypeEnum.UNIVERSITY.name,
        ],
    ),
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
    valuated_from_trainings = serializers.SerializerMethodField()
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
            'fwb_equivalent_program',
            'with_complement',
            'complement_registered_credit_number',
            'complement_acquired_credit_number',
            'block_1_acquired_credit_number',
        ]
        read_only_fields = ['external_id']

    @staticmethod
    @extend_schema_field(serializers.ListSerializer(child=serializers.CharField()))
    def get_valuated_from_trainings(value):
        return [
            AnneeInscriptionFormationTranslator.ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE.get(training_type)
            for training_type in getattr(value, 'valuated_from_trainings', [])
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
            'result',
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
            'valuated_from_trainings',
            'country',
            'obtained_diploma',
            'external_id',
        ]
        read_only_fields = ['external_id']


class DoctoratCompleterCurriculumCommandSerializer(DTOSerializer):
    reponses_questions_specifiques = AnswerToSpecificQuestionField()
    auteur_modification = None

    class Meta:
        source = doctorate_commands.CompleterCurriculumCommand
        fields = [
            'curriculum',
            'reponses_questions_specifiques',
        ]


class ContinuingEducationCompleterCurriculumCommandSerializer(DTOSerializer):
    reponses_questions_specifiques = AnswerToSpecificQuestionField()
    auteur_modification = None

    class Meta:
        source = continuing_commands.CompleterCurriculumCommand
        fields = [
            'curriculum',
            'equivalence_diplome',
            'reponses_questions_specifiques',
        ]


class GeneralEducationCompleterCurriculumCommandSerializer(DTOSerializer):
    reponses_questions_specifiques = AnswerToSpecificQuestionField()
    auteur_modification = None

    class Meta:
        source = general_commands.CompleterCurriculumCommand
        fields = [
            'curriculum',
            'equivalence_diplome',
            'reponses_questions_specifiques',
        ]


class CurriculumDetailsSerializer(serializers.Serializer):
    professional_experiences = LiteProfessionalExperienceSerializer(many=True)
    educational_experiences = LiteEducationalExperienceSerializer(many=True)
    minimal_date = serializers.SerializerMethodField()
    maximal_date = serializers.SerializerMethodField()
    incomplete_periods = serializers.ListField(child=serializers.CharField())
    incomplete_experiences = serializers.DictField(child=serializers.ListField(child=serializers.CharField()))
    incomplete_professional_experiences = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField())
    )

    @extend_schema_field(OpenApiTypes.DATE)
    def get_minimal_date(self, _):
        current_year = current_academic_year()
        return ProfilCandidatTranslator.get_annees_minimum_curriculum(
            global_id=self.context.get('related_person').global_id,
            current_year=current_year.year,
        ).get('minimal_date')

    @extend_schema_field(OpenApiTypes.DATE)
    def get_maximal_date(self, _):
        return ProfilCandidatTranslator.get_date_maximale_curriculum(
            mois_debut_annee_academique_courante_facultatif=self.context.get(
                'current_academic_year_start_month_is_facultative',
                False,
            )
        )
