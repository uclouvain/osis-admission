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
from functools import partial

from django.utils.functional import cached_property
from rest_framework import serializers

from admission.api.serializers.fields import AnswerToSpecificQuestionField
from admission.infrastructure.admission.domain.service.profil_candidat import (
    ProfilCandidatTranslator,
)
from base.api.serializers.academic_year import RelatedAcademicYearField
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.models.enums.got_diploma import CHOIX_DIPLOME_OBTENU, GotDiploma
from base.models.organization import Organization
from osis_profile.models import (
    BelgianHighSchoolDiploma,
    ForeignHighSchoolDiploma,
    HighSchoolDiplomaAlternative,
)
from reference.api.serializers.country import RelatedCountryField
from reference.api.serializers.language import RelatedLanguageField

RelatedHighSchoolField = partial(
    serializers.SlugRelatedField,
    slug_field='uuid',
    queryset=Organization.objects.filter(establishment_type=EstablishmentTypeEnum.HIGH_SCHOOL.name),
)


class BelgianHighSchoolDiplomaSerializer(serializers.ModelSerializer):
    academic_graduation_year = RelatedAcademicYearField()
    institute = RelatedHighSchoolField(required=False, allow_null=True)

    class Meta:
        model = BelgianHighSchoolDiploma
        fields = (
            "academic_graduation_year",
            "high_school_diploma",
            "community",
            "educational_type",
            "educational_other",
            "institute",
            "other_institute_name",
            "other_institute_address",
        )


class ForeignHighSchoolDiplomaSerializer(serializers.ModelSerializer):
    linguistic_regime = RelatedLanguageField()
    country = RelatedCountryField()
    academic_graduation_year = RelatedAcademicYearField()

    class Meta:
        model = ForeignHighSchoolDiploma
        fields = (
            "academic_graduation_year",
            "high_school_transcript",
            "high_school_diploma",
            "foreign_diploma_type",
            "linguistic_regime",
            "other_linguistic_regime",
            "country",
            "equivalence",
            "high_school_transcript_translation",
            "high_school_diploma_translation",
            "final_equivalence_decision_ue",
            "access_diploma_to_higher_education_ue",
            "final_equivalence_decision_not_ue",
            "access_diploma_to_higher_education_not_ue",
            "equivalence_decision_proof",
        )


class HighSchoolDiplomaAlternativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HighSchoolDiplomaAlternative
        fields = ("first_cycle_admission_exam",)


class HighSchoolDiplomaSerializer(serializers.Serializer):
    graduated_from_high_school = serializers.ChoiceField(required=False, allow_blank=True, choices=GotDiploma.choices())
    graduated_from_high_school_year = RelatedAcademicYearField(required=False, allow_null=True)
    belgian_diploma = BelgianHighSchoolDiplomaSerializer(required=False, allow_null=True)
    foreign_diploma = ForeignHighSchoolDiplomaSerializer(required=False, allow_null=True)
    high_school_diploma_alternative = HighSchoolDiplomaAlternativeSerializer(required=False, allow_null=True)
    specific_question_answers = AnswerToSpecificQuestionField(write_only=True)
    is_vae_potential = serializers.SerializerMethodField(read_only=True)
    is_valuated = serializers.SerializerMethodField(read_only=True)
    can_update_diploma = serializers.SerializerMethodField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_vae_potential'].field_schema = {'type': 'boolean'}
        self.fields['is_valuated'].field_schema = {'type': 'boolean'}
        self.fields['can_update_diploma'].field_schema = {'type': 'boolean'}

    def get_is_vae_potential(self, person):
        return ProfilCandidatTranslator.est_potentiel_vae(person.global_id)

    def get_is_valuated(self, person):
        return self.valuation.est_valorise

    @staticmethod
    def load_diploma(instance):
        instance.belgian_diploma = BelgianHighSchoolDiploma.objects.filter(person=instance).first()
        instance.foreign_diploma = ForeignHighSchoolDiploma.objects.filter(person=instance).first()
        instance.high_school_diploma_alternative = HighSchoolDiplomaAlternative.objects.filter(person=instance).first()

    def to_representation(self, instance):
        self.load_diploma(instance)
        return super().to_representation(instance)

    @staticmethod
    def update_belgian_diploma(instance, belgian_diploma_data):
        BelgianHighSchoolDiploma.objects.update_or_create(person=instance, defaults=belgian_diploma_data)
        HighSchoolDiplomaSerializer.clean_foreign_diploma(instance)
        HighSchoolDiplomaSerializer.clean_high_school_diploma_alternative(instance)

    @staticmethod
    def update_foreign_diploma(instance, foreign_diploma_data):
        ForeignHighSchoolDiploma.objects.update_or_create(person=instance, defaults=foreign_diploma_data)
        HighSchoolDiplomaSerializer.clean_belgian_diploma(instance)
        HighSchoolDiplomaSerializer.clean_high_school_diploma_alternative(instance)

    @staticmethod
    def update_high_school_diploma_alternative(instance, high_school_diploma_alternative_data):
        HighSchoolDiplomaAlternative.objects.update_or_create(
            person=instance,
            defaults=high_school_diploma_alternative_data,
        )
        HighSchoolDiplomaSerializer.clean_belgian_diploma(instance)
        HighSchoolDiplomaSerializer.clean_foreign_diploma(instance)

    @staticmethod
    def clean_foreign_diploma(instance):
        if instance.foreign_diploma:
            instance.foreign_diploma.delete()

    @staticmethod
    def clean_belgian_diploma(instance):
        if instance.belgian_diploma:
            instance.belgian_diploma.delete()

    @staticmethod
    def clean_high_school_diploma_alternative(instance):
        if instance.high_school_diploma_alternative:
            instance.high_school_diploma_alternative.delete()

    def get_can_update_diploma(self, person):
        return self.valuation.diplome_est_modifiable(
            diplome=(
                self.instance.belgian_diploma
                or self.instance.foreign_diploma
                or self.instance.high_school_diploma_alternative
            ),
            formation=self.context.get('training_type'),
        )

    @cached_property
    def valuation(self):
        return ProfilCandidatTranslator.valorisation_etudes_secondaires(matricule=self.instance.global_id)

    def update(self, instance, validated_data):
        self.load_diploma(instance)

        if not self.get_is_valuated(instance):
            # The base data can only be updated if the secondary studies are not valuated
            instance.graduated_from_high_school = validated_data.get('graduated_from_high_school')
            instance.graduated_from_high_school_year = validated_data.get('graduated_from_high_school_year')
            instance.save()

        # The diploma data can only be updated in a specific case for the admissions for a bachelor
        if not self.get_can_update_diploma(instance):
            return instance

        belgian_diploma_data = validated_data.get("belgian_diploma")
        foreign_diploma_data = validated_data.get("foreign_diploma")
        high_school_diploma_alternative_data = validated_data.get("high_school_diploma_alternative")

        if belgian_diploma_data:
            self.update_belgian_diploma(instance, belgian_diploma_data)
        elif foreign_diploma_data:
            self.update_foreign_diploma(instance, foreign_diploma_data)
        elif high_school_diploma_alternative_data:
            self.update_high_school_diploma_alternative(instance, high_school_diploma_alternative_data)
        else:
            if instance.graduated_from_high_school not in CHOIX_DIPLOME_OBTENU:
                self.clean_belgian_diploma(instance)
                self.clean_foreign_diploma(instance)
            else:
                for diploma in [instance.belgian_diploma, instance.foreign_diploma]:
                    if diploma and diploma.academic_graduation_year != instance.graduated_from_high_school_year:
                        diploma.academic_graduation_year = instance.graduated_from_high_school_year
                        diploma.save(update_fields=['academic_graduation_year'])

            if instance.graduated_from_high_school != GotDiploma.NO.name:
                self.clean_high_school_diploma_alternative(instance)
        return instance
