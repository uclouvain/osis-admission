from rest_framework import serializers

from osis_profile.models import BelgianHighSchoolDiploma, ForeignHighSchoolDiploma


class BelgianHighSchoolDiplomaSerializer(serializers.ModelSerializer):
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
    belgian_diploma = BelgianHighSchoolDiplomaSerializer(
        required=False, allow_null=True
    )
    foreign_diploma = ForeignHighSchoolDiplomaSerializer(
        required=False, allow_null=True
    )

    @staticmethod
    def load_diploma(instance):
        instance.belgian_diploma = BelgianHighSchoolDiploma.objects.filter(
            person=instance
        ).first()
        instance.foreign_diploma = ForeignHighSchoolDiploma.objects.filter(
            person=instance
        ).first()

    def to_representation(self, instance):
        self.load_diploma(instance)
        return super().to_representation(instance)
