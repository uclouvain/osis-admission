from django.views.generic import ListView

from admission.contrib.models import AdmissionDoctorate


class AdmissionDoctorateListView(ListView):
    model = AdmissionDoctorate
    template_name = "admission/doctorat/admissiondoctorat_list.html"
