import factory

from admission.contrib.models import AdmissionDoctorate


class AdmissionDoctorateFactory(factory.DjangoModelFactory):
    class Meta:
        model = AdmissionDoctorate
