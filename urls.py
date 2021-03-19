from django.urls import path

from .contrib.views import AdmissionDoctorateListView


app_name = "admissions"
urlpatterns = [
    path('doctorates/', AdmissionDoctorateListView.as_view(), name="doctorate-list"),
]
