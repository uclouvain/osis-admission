from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication

from admission.contrib.models import AdmissionDoctorate
from admission.contrib.serializers import AdmissionDoctorateSerializer


class AdmissionDoctorateViewSet(viewsets.ModelViewSet):
    serializer_class = AdmissionDoctorateSerializer
    queryset = AdmissionDoctorate.objects.all()
    authentication_classes = [SessionAuthentication, ]
    lookup_field = "uuid"
