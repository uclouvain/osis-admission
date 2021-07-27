# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################

from django.urls import path, include

from .contrib.views import (
    DoctorateAdmissionCreateView,
    DoctorateAdmissionDeleteView,
    DoctorateAdmissionDetailView,
    DoctorateAdmissionListView,
    DoctorateAdmissionUpdateView,
    autocomplete,
)

app_name = "admissions"
urlpatterns = [
    path("doctorates/", DoctorateAdmissionListView.as_view(), name="doctorate-list"),
    path(
        "doctorates/create/",
        DoctorateAdmissionCreateView.as_view(),
        name="doctorate-create",
    ),
    path(
        "doctorates/<pk>/",
        DoctorateAdmissionDetailView.as_view(),
        name="doctorate-detail",
    ),
    path(
        "doctorates/<pk>/delete/",
        DoctorateAdmissionDeleteView.as_view(),
        name="doctorate-delete",
    ),
    path(
        "doctorates/<pk>/update/",
        DoctorateAdmissionUpdateView.as_view(),
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
