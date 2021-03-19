from rest_framework import serializers

from admission.contrib.models import AdmissionDoctorate


class AdmissionDoctorateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionDoctorate
        fields = [
            "uuid",
            "type",
            "candidate",
            "comment",
            "author",
            "created",
            "modified",
        ]
