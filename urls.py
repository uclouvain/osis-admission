from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .contrib.api.doctorate import AdmissionDoctorateViewSet
from .contrib.views import (
    AdmissionDoctorateCreateView,
    AdmissionDoctorateDeleteView,
    AdmissionDoctorateDetailView,
    AdmissionDoctorateListView,
    AdmissionDoctorateUpdateView,
    autocomplete,
)

router = DefaultRouter()
router.register(r'api/v1', AdmissionDoctorateViewSet, basename='doctorate-api')
urlpatterns = router.urls

app_name = "admissions"
urlpatterns += [
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
