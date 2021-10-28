from rest_framework import serializers

from base.api.serializers.academic_year import RelatedAcademicYearField
from osis_profile.models import BelgianHighSchoolDiploma, ForeignHighSchoolDiploma
from osis_profile.models.education import Schedule
from reference.api.serializers.country import RelatedCountryField
from reference.api.serializers.language import RelatedLanguageField


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = "__all__"


class BelgianHighSchoolDiplomaSerializer(serializers.ModelSerializer):
    academic_graduation_year = RelatedAcademicYearField()
    schedule = ScheduleSerializer(required=False, allow_null=True)

    class Meta:
        model = BelgianHighSchoolDiploma
        fields = (
            "academic_graduation_year",
            "result",
            "community",
            "educational_type",
            "educational_other",
            "course_repeat",
            "course_orientation",
            "institute",
            "other_institute",
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
            "result",
            "foreign_diploma_type",
            "linguistic_regime",
            "other_linguistic_regime",
            "country",
        )


class HighSchoolDiplomaSerializer(serializers.Serializer):
    belgian_diploma = BelgianHighSchoolDiplomaSerializer(required=False, allow_null=True)
    foreign_diploma = ForeignHighSchoolDiplomaSerializer(required=False, allow_null=True)

    @staticmethod
    def load_diploma(instance):
        instance.belgian_diploma = BelgianHighSchoolDiploma.objects.filter(person=instance).first()
        instance.foreign_diploma = ForeignHighSchoolDiploma.objects.filter(person=instance).first()

    def to_representation(self, instance):
        self.load_diploma(instance)
        return super().to_representation(instance)

    def update(self, instance, validated_data):
        self.load_diploma(instance)
        belgian_diploma_data = validated_data.get("belgian_diploma")
        foreign_diploma_data = validated_data.get("foreign_diploma")
        if belgian_diploma_data:
            pk = instance.belgian_diploma and instance.belgian_diploma.schedule_id
            schedule, _ = Schedule.objects.update_or_create(pk=pk, defaults=belgian_diploma_data.get("schedule"))
            belgian_diploma_data["schedule"] = schedule
            BelgianHighSchoolDiploma.objects.update_or_create(person=instance, defaults=belgian_diploma_data)
            if instance.foreign_diploma:
                instance.foreign_diploma.delete()
        elif foreign_diploma_data:
            ForeignHighSchoolDiploma.objects.update_or_create(person=instance, defaults=foreign_diploma_data)
            if instance.belgian_diploma:
                instance.belgian_diploma.delete()
                instance.belgian_diploma.schedule.delete()
        else:
            if instance.foreign_diploma:
                instance.foreign_diploma.delete()
            if instance.belgian_diploma:
                instance.belgian_diploma.delete()
                instance.belgian_diploma.schedule.delete()
        return instance
