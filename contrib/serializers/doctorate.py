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
        candidate = validated_data.pop("candidate").id
        admission_type = validated_data.pop("type")
        author = self.context["request"].user.person
        return AdmissionDoctorate.objects.create(
            candidate_id=candidate,
            author=author,
            type=admission_type,
            **validated_data,
        )

    def update(self, instance, validated_data):
        candidate = validated_data.pop("candidate", None)
        admission_type = validated_data.pop("type", None)
        comment = validated_data.pop("comment", None)
        if candidate:
            instance.candidate = candidate
        if admission_type:
            instance.type = AdmissionType.get_value(admission_type)
        if comment:
            instance.comment = comment
        instance.save()
        return instance

    class Meta:
        model = AdmissionDoctorate
        fields = [
            "type",
            "candidate",
            "comment",
        ]
