# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.urls import include, path as _path
from rest_framework.routers import SimpleRouter

from admission.api import views


def path(pattern, view, name=None):
    return _path(pattern, view.as_view(), name=getattr(view, 'name', name))


# Create a router and register our viewsets with it.
view_set_router = SimpleRouter(trailing_slash=False)
view_set_router.register(
    'curriculum/educational',
    views.EducationalExperienceViewSet,
    basename="cv_educational_experiences",
)
view_set_router.register(
    'curriculum/professional',
    views.ProfessionalExperienceViewSet,
    basename="cv_professional_experiences",
)

app_name = "admission_api_v1"

person_tabs = [
    path('person', views.PersonViewSet),
    path('coordonnees', views.CoordonneesViewSet),
    path('secondary_studies', views.SecondaryStudiesViewSet),
    path('languages_knowledge', views.LanguagesKnowledgeViewSet),
    path('curriculum/file', views.CurriculumFileView),
    path('curriculum/', views.CurriculumView),
    _path('', include(view_set_router.urls)),
]

urlpatterns = [
    # Lists
    path('dashboard', views.DashboardViewSet),
    path('propositions', views.PropositionListView),
    path('supervised_propositions', views.SupervisedPropositionListView),
    # Creation tabs
    _path('', include(person_tabs)),
    # Admission-related
    path('propositions/<uuid:uuid>', views.PropositionViewSet),
    _path('propositions/<uuid:uuid>/', include(person_tabs)),
    path('propositions/<uuid:uuid>/verify_project', views.VerifyProjectView),
    path('propositions/<uuid:uuid>/submit', views.SubmitPropositionViewSet),
    path('propositions/<uuid:uuid>/cotutelle', views.CotutelleAPIView),
    path('propositions/<uuid:uuid>/accounting', views.AccountingView),
    # Supervision
    path('propositions/<uuid:uuid>/supervision', views.SupervisionAPIView),
    path('propositions/<uuid:uuid>/supervision/set-reference-promoter', views.SupervisionSetReferencePromoterAPIView),
    path('propositions/<uuid:uuid>/supervision/request-signatures', views.RequestSignaturesAPIView),
    path('propositions/<uuid:uuid>/supervision/approve', views.ApprovePropositionAPIView),
    path('propositions/<uuid:uuid>/supervision/approve-by-pdf', views.ApproveByPdfPropositionAPIView),
    # Submission confirmation
    path('propositions/<uuid:uuid>/confirmation', views.ConfirmationAPIView),
    path('propositions/<uuid:uuid>/confirmation/last', views.LastConfirmationAPIView),
    path('propositions/<uuid:uuid>/confirmation/last/canvas', views.LastConfirmationCanvasAPIView),
    path('propositions/<uuid:uuid>/supervised_confirmation', views.SupervisedConfirmationAPIView),
    # Doctorate
    path('propositions/<uuid:uuid>/doctorate', views.DoctorateAPIView),
    path('propositions/<uuid:uuid>/training', views.DoctoralTrainingListView),
    path('propositions/<uuid:uuid>/training/config', views.DoctoralTrainingConfigView),
    path('propositions/<uuid:uuid>/training/submit', views.DoctoralTrainingSubmitView),
    path('propositions/<uuid:uuid>/training/<uuid:activity_id>', views.DoctoralTrainingView),
    path('propositions/<uuid:uuid>/training/<uuid:activity_id>/assent', views.DoctoralTrainingAssentView),
    # Autocompletes
    path('autocomplete/sector', views.AutocompleteSectorView),
    path('autocomplete/sector/<str:sigle>/doctorates', views.AutocompleteDoctoratView),
    path('autocomplete/tutor', views.AutocompleteTutorView),
    path('autocomplete/person', views.AutocompletePersonView),
]
