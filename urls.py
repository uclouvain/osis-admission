from django.urls import path, include

from .contrib.views import AdmissionDoctorateListView, autocomplete

app_name = "admissions"
urlpatterns = [
    path('doctorates/', AdmissionDoctorateListView.as_view(), name="doctorate-list"),

    path('autocomplete/', include(
        [
            path(
                "person/",
                autocomplete.PersonAutocomplete.as_view(),
                name="person_autocomplete",
            ),
        ]
    )),
]
