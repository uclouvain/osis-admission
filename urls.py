from django.urls import path, include

from .contrib.views import (
    AdmissionDoctorateCreateView,
    AdmissionDoctorateDetailView,
    AdmissionDoctorateListView,
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

    path("autocomplete/", include(
        [
            path(
                "person/",
                autocomplete.PersonAutocomplete.as_view(),
                name="person_autocomplete",
            ),
        ]
    )),
]
