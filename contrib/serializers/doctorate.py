from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from admission.contrib.models import AdmissionDoctorate, AdmissionType
from base.models.person import Person


class AdmissionDoctorateSerializer(serializers.ModelSerializer):
    url = serializers.URLField(source="get_absolute_url", read_only=True)
    type = serializers.CharField(source="get_type_display", read_only=True)
    type_select = serializers.ChoiceField(
        choices=AdmissionType.choices(), write_only=True
    )
    candidate = serializers.StringRelatedField(read_only=True)
    candidate_write = serializers.PrimaryKeyRelatedField(
        label=_("Candidate"), queryset=Person.objects.all(), write_only=True
    )
    author = serializers.StringRelatedField(read_only=True)

    def create(self, validated_data):
        candidate_write = validated_data.pop("candidate_write").id
        type_select = validated_data.pop("type_select")
        author = self.context["request"].user.person
        admission_doctorate = AdmissionDoctorate.objects.create(
            candidate_id=candidate_write,
            author=author,
            type=type_select,
            **validated_data,
        )
        return admission_doctorate

    def update(self, instance, validated_data):
        candidate_write = validated_data.pop("candidate_write", None)
        type_select = validated_data.pop("type_select", None)
        comment = validated_data.pop("comment", None)
        if candidate_write:
            instance.candidate = candidate_write
        if type_select:
            instance.type = AdmissionType.get_value(type_select)
        if comment:
            instance.comment = comment
        instance.save()
        return instance

    class Meta:
        model = AdmissionDoctorate
        fields = [
            "uuid",
            "url",
            "type",
            "type_select",
            "candidate",
            "candidate_write",
            "comment",
            "author",
            "created",
            "modified",
        ]
