from django.urls import path, include

from .contrib.views import (
    AdmissionDoctorateCreateView,
    AdmissionDoctorateDeleteView,
    AdmissionDoctorateDetailView,
    AdmissionDoctorateListView,
    AdmissionDoctorateUpdateView,
    autocomplete,
)

app_name = "admissions"
urlpatterns = [
    path("doctorates/", AdmissionDoctorateListView.as_view(), name="doctorate-list"),
    path(
        "doctorates/create/",
        AdmissionDoctorateCreateView.as_view(),
        name="doctorate-create",
    ),
    path(
        "doctorates/<pk>/",
        AdmissionDoctorateDetailView.as_view(),
        name="doctorate-detail",
    ),
    path(
        "doctorates/<pk>/delete/",
        AdmissionDoctorateDeleteView.as_view(),
        name="doctorate-delete",
    ),
    path(
        "doctorates/<pk>/update/",
        AdmissionDoctorateUpdateView.as_view(),
        name="doctorate-update",
    ),

    path("autocomplete/", include(
        [
            path(
                "person/",
                autocomplete.PersonAutocomplete.as_view(),
                name="person-autocomplete",
            ),
            path(
                "candidate/",
                autocomplete.CandidateAutocomplete.as_view(),
                name="candidate-autocomplete",
            ),
        ]
    )),
]
