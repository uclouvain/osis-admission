import django_filters as filters

from admission.contrib.models import AdmissionDoctorate


class AdmissionDoctorateFilter(filters.FilterSet):

    class Meta:
        model = AdmissionDoctorate
        fields = [
            "type",
        ]
