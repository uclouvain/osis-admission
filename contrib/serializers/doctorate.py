from rest_framework import serializers

from admission.contrib.models import AdmissionDoctorate
from base.models.person import Person


class PersonSerializer(serializers.ModelSerializer):
    str = serializers.CharField(source="__str__")

    class Meta:
        model = Person
        fields = ['str', ]


class AdmissionDoctorateSerializer(serializers.ModelSerializer):
    url = serializers.URLField(source="get_absolute_url")
    type = serializers.CharField(source="get_type_display")
    candidate = PersonSerializer()
    author = PersonSerializer()

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
