from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response

from admission.contrib.models import AdmissionDoctorate
from admission.contrib.serializers import (
    AdmissionDoctorateReadSerializer, AdmissionDoctorateWriteSerializer
)


class AdmissionDoctorateViewSet(viewsets.ModelViewSet):
    queryset = AdmissionDoctorate.objects.all()
    authentication_classes = [SessionAuthentication, ]
    lookup_field = "uuid"

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return AdmissionDoctorateWriteSerializer
        return AdmissionDoctorateReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serializer = AdmissionDoctorateReadSerializer(instance=serializer.instance)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )
