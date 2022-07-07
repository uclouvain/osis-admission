from functools import partial

from rest_framework import serializers

from base.api.serializers.academic_year import RelatedAcademicYearField
from osis_profile.models import BelgianHighSchoolDiploma, ForeignHighSchoolDiploma, HighSchoolDiplomaAlternative
from osis_profile.models.education import Schedule
from osis_profile.models.enums.education import EducationalType
from reference.api.serializers.country import RelatedCountryField
from reference.api.serializers.language import RelatedLanguageField
from reference.models.high_school import HighSchool


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'


RelatedHighSchoolField = partial(
    serializers.SlugRelatedField,
    slug_field='uuid',
    queryset=HighSchool.objects.all(),
)


class BelgianHighSchoolDiplomaSerializer(serializers.ModelSerializer):
    academic_graduation_year = RelatedAcademicYearField()
    schedule = ScheduleSerializer(required=False, allow_null=True)
    institute = RelatedHighSchoolField(required=False, allow_null=True)

    class Meta:
        model = BelgianHighSchoolDiploma
        fields = (
            "academic_graduation_year",
            "high_school_diploma",
            "enrolment_certificate",
            "result",
            "community",
            "educational_type",
            "educational_other",
            "institute",
            "other_institute_name",
            "other_institute_address",
            "schedule",
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
            "enrolment_certificate",
            "result",
            "foreign_diploma_type",
            "linguistic_regime",
            "other_linguistic_regime",
            "country",
            "equivalence",
            "high_school_transcript_translation",
            "high_school_diploma_translation",
            "enrolment_certificate_translation",
            "final_equivalence_decision",
            "equivalence_decision_proof",
            "restrictive_equivalence_daes",
            "restrictive_equivalence_admission_test",
        )


class HighSchoolDiplomaAlternativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HighSchoolDiplomaAlternative
        fields = (
            "first_cycle_admission_exam",
        )


class HighSchoolDiplomaSerializer(serializers.Serializer):
    belgian_diploma = BelgianHighSchoolDiplomaSerializer(required=False, allow_null=True)
    foreign_diploma = ForeignHighSchoolDiplomaSerializer(required=False, allow_null=True)
    high_school_diploma_alternative = HighSchoolDiplomaAlternativeSerializer(required=False, allow_null=True)

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
        schedule_data = belgian_diploma_data.pop("schedule", None)
        educational_types_that_require_schedule = [
            EducationalType.TEACHING_OF_GENERAL_EDUCATION.name,
            EducationalType.TRANSITION_METHOD.name,
            EducationalType.ARTISTIC_TRANSITION.name,
        ]
        educational_type_data = belgian_diploma_data.get("educational_type")
        if schedule_data and educational_type_data in educational_types_that_require_schedule:
            pk = instance.belgian_diploma and instance.belgian_diploma.schedule_id
            schedule, _ = Schedule.objects.update_or_create(pk=pk, defaults=schedule_data)
            belgian_diploma_data["schedule"] = schedule
        elif instance.belgian_diploma and instance.belgian_diploma.schedule:
            instance.belgian_diploma.schedule.delete()  # schedule is not needed anymore

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
            if instance.belgian_diploma.schedule:
                instance.belgian_diploma.schedule.delete()

    @staticmethod
    def clean_high_school_diploma_alternative(instance):
        if instance.high_school_diploma_alternative:
            instance.high_school_diploma_alternative.delete()

    def update(self, instance, validated_data):
        self.load_diploma(instance)

        belgian_diploma_data = validated_data.get("belgian_diploma")
        foreign_diploma_data = validated_data.get("foreign_diploma")
        high_school_diploma_alternative_data = validated_data.get("high_school_diploma_alternative")

        if belgian_diploma_data:
            self.update_belgian_diploma(instance, belgian_diploma_data)
        elif foreign_diploma_data:
            self.update_foreign_diploma(instance, foreign_diploma_data)
        elif high_school_diploma_alternative_data:
            self.update_high_school_diploma_alternative(instance, high_school_diploma_alternative_data)
        else:  # if no data given, it means that the user don't have a diploma, so delete any previously saved ones
            self.clean_belgian_diploma(instance)
            self.clean_foreign_diploma(instance)
            self.clean_high_school_diploma_alternative(instance)
        return instance
