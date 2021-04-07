from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from admission.contrib.models import AdmissionDoctorate, AdmissionType
from base.models.person import Person


class AdmissionDoctorateReadSerializer(serializers.ModelSerializer):
    url = serializers.ReadOnlyField(source="get_absolute_url")
    type = serializers.ReadOnlyField(source="get_type_display")
    candidate = serializers.StringRelatedField()
    author = serializers.StringRelatedField()

    class Meta:
        model = AdmissionDoctorate
        fields = [
            "uuid",
            "url",
            "type",
            "candidate",
            "comment",
            "author",
            "created",
            "modified",
        ]


class AdmissionDoctorateWriteSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=AdmissionType.choices())
    candidate = serializers.PrimaryKeyRelatedField(
        label=_("Candidate"), queryset=Person.objects.all()
    )

    def create(self, validated_data):
        validated_data['author'] = self.context["request"].user.person
        return super().create(validated_data)

    class Meta:
        model = AdmissionDoctorate
        fields = [
            "type",
            "candidate",
            "comment",
        ]
