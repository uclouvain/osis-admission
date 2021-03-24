from rest_framework import serializers

from admission.contrib.models import AdmissionDoctorate


class AdmissionDoctorateSerializer(serializers.ModelSerializer):
    url = serializers.URLField(source="get_absolute_url")
    type = serializers.CharField(source="get_type_display")
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
