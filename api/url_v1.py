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


# Create the routers and register our viewsets with it.
doctorate_view_set_router = SimpleRouter(trailing_slash=False)
doctorate_view_set_router.register(
    'curriculum/educational',
    views.EducationalExperienceViewSet,
    basename="cv_educational_experiences",
)
doctorate_view_set_router.register(
    'curriculum/professional',
    views.ProfessionalExperienceViewSet,
    basename="cv_professional_experiences",
)

general_education_view_set_router = SimpleRouter(trailing_slash=False)
general_education_view_set_router.register(
    'curriculum/educational',
    views.GeneralEducationalExperienceViewSet,
    basename="general_cv_educational_experiences",
)
general_education_view_set_router.register(
    'curriculum/professional',
    views.GeneralProfessionalExperienceViewSet,
    basename="general_cv_professional_experiences",
)

continuing_education_view_set_router = SimpleRouter(trailing_slash=False)
continuing_education_view_set_router.register(
    'curriculum/educational',
    views.ContinuingEducationalExperienceViewSet,
    basename="continuing_cv_educational_experiences",
)
continuing_education_view_set_router.register(
    'curriculum/professional',
    views.ContinuingProfessionalExperienceViewSet,
    basename="continuing_cv_professional_experiences",
)
app_name = "admission_api_v1"

person_tabs = [
    path('person', views.PersonViewSet),
    path('coordonnees', views.CoordonneesViewSet),
    path('secondary_studies', views.SecondaryStudiesViewSet),
    path('languages_knowledge', views.LanguagesKnowledgeViewSet),
    path('curriculum/file', views.CurriculumFileView),
    path('curriculum/', views.CurriculumView),
    _path('', include(doctorate_view_set_router.urls)),
]

urlpatterns = [
    # > Every education
    path('dashboard', views.DashboardViewSet),
    path('propositions', views.PropositionListView),
    # > Doctorate education
    path('supervised_propositions', views.SupervisedPropositionListView),
    # Creation tabs
    _path('', include(person_tabs)),
    # Admission-related
    path('propositions/doctorate/<uuid:uuid>', views.PropositionViewSet),
    _path('propositions/doctorate/<uuid:uuid>/', include(person_tabs)),
    path('propositions/doctorate/<uuid:uuid>/verify_project', views.VerifyProjectView),
    path('propositions/doctorate/<uuid:uuid>/submit', views.SubmitPropositionViewSet),
    path('propositions/doctorate/<uuid:uuid>/cotutelle', views.CotutelleAPIView),
    path('propositions/doctorate/<uuid:uuid>/accounting', views.AccountingView),
    path('propositions/doctorate/<uuid:uuid>/training_choice', views.DoctorateUpdateAdmissionTypeAPIView),
    # Supervision
    path('propositions/doctorate/<uuid:uuid>/supervision', views.SupervisionAPIView),
    path(
        'propositions/doctorate/<uuid:uuid>/supervision/set-reference-promoter',
        views.SupervisionSetReferencePromoterAPIView,
    ),
    path('propositions/doctorate/<uuid:uuid>/supervision/request-signatures', views.RequestSignaturesAPIView),
    path('propositions/doctorate/<uuid:uuid>/supervision/approve', views.ApprovePropositionAPIView),
    path('propositions/doctorate/<uuid:uuid>/supervision/approve-by-pdf', views.ApproveByPdfPropositionAPIView),
    # Submission confirmation
    path('propositions/doctorate/<uuid:uuid>/confirmation', views.ConfirmationAPIView),
    path('propositions/doctorate/<uuid:uuid>/confirmation/last', views.LastConfirmationAPIView),
    path('propositions/doctorate/<uuid:uuid>/confirmation/last/canvas', views.LastConfirmationCanvasAPIView),
    path('propositions/doctorate/<uuid:uuid>/supervised_confirmation', views.SupervisedConfirmationAPIView),
    # Doctorate
    path('propositions/doctorate/<uuid:uuid>/doctorate', views.DoctorateAPIView),
    # Training
    path('propositions/doctorate/<uuid:uuid>/training/config', views.TrainingConfigView),
    path('propositions/doctorate/<uuid:uuid>/doctoral-training', views.DoctoralTrainingListView),
    path('propositions/doctorate/<uuid:uuid>/training/submit', views.TrainingSubmitView),
    path('propositions/doctorate/<uuid:uuid>/training/assent', views.TrainingAssentView),
    path('propositions/doctorate/<uuid:uuid>/training/<uuid:activity_id>', views.TrainingView),
    path('propositions/doctorate/<uuid:uuid>/complementary-training', views.ComplementaryTrainingListView),
    path('propositions/doctorate/<uuid:uuid>/course-enrollment', views.CourseEnrollmentListView),
    # > General education
    path('propositions/general-education', views.GeneralTrainingChoiceAPIView),
    path('propositions/general-education/<uuid:uuid>', views.GeneralPropositionViewSet),
    path('propositions/general-education/<uuid:uuid>/training-choice', views.GeneralUpdateTrainingChoiceAPIView),
    path('propositions/general-education/<uuid:uuid>/person', views.GeneralPersonViewSet),
    path('propositions/general-education/<uuid:uuid>/coordonnees', views.GeneralCoordonneesViewSet),
    path('propositions/general-education/<uuid:uuid>/secondary-studies', views.GeneralSecondaryStudiesViewSet),
    path('propositions/general-education/<uuid:uuid>/curriculum/file', views.GeneralCurriculumFileView),
    path('propositions/general-education/<uuid:uuid>/curriculum/', views.GeneralCurriculumView),
    _path('propositions/general-education/<uuid:uuid>/', include(general_education_view_set_router.urls)),
    # > Continuing education
    path('propositions/continuing-education', views.ContinuingTrainingChoiceAPIView),
    path('propositions/continuing-education/<uuid:uuid>', views.ContinuingPropositionViewSet),
    path('propositions/continuing-education/<uuid:uuid>/training-choice', views.ContinuingUpdateTrainingChoiceAPIView),
    path('propositions/continuing-education/<uuid:uuid>/person', views.ContinuingPersonViewSet),
    path('propositions/continuing-education/<uuid:uuid>/coordonnees', views.ContinuingCoordonneesViewSet),
    path('propositions/continuing-education/<uuid:uuid>/secondary-studies', views.ContinuingSecondaryStudiesViewSet),
    path('propositions/continuing-education/<uuid:uuid>/curriculum/file', views.ContinuingCurriculumFileView),
    path('propositions/continuing-education/<uuid:uuid>/curriculum/', views.ContinuingCurriculumView),
    _path('propositions/continuing-education/<uuid:uuid>/', include(continuing_education_view_set_router.urls)),
    # Autocompletes
    path('autocomplete/sector', views.AutocompleteSectorView),
    path('autocomplete/sector/<str:sigle>/doctorates', views.AutocompleteDoctoratView),
    path('autocomplete/general-education', views.AutocompleteGeneralEducationView),
    path('autocomplete/continuing-education', views.AutocompleteContinuingEducationView),
    path('autocomplete/tutor', views.AutocompleteTutorView),
    path('autocomplete/person', views.AutocompletePersonView),
    path('autocomplete/<str:scholarship_type>/scholarship', views.AutocompleteScholarshipView),
    # Others
    path('scholarship/<uuid:uuid>', views.RetrieveScholarshipView),
    path('campus', views.ListCampusView),
    path('campus/<uuid:uuid>', views.RetrieveCampusView),
]
