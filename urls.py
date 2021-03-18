from django.urls import path

from admission.contrib.views import AdmissionDoctorateListView


app_name = "admissions"
urlpatterns = [
    path('doctorats', AdmissionDoctorateListView.as_view(), name="doctorate-list"),
]
