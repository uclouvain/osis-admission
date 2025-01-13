# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.urls import include
from django.urls import path as _path
from rest_framework.routers import SimpleRouter

import admission.api.views.submission
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
    _path('', include(doctorate_view_set_router.urls)),
]

urlpatterns = [
    # > Every education
    path('dashboard', views.DashboardViewSet),
    path('propositions', views.PropositionListView),
    path('propositions/permissions', views.PropositionCreatePermissionsView),
    path('identification', views.IdentificationDTOView, views.IdentificationDTOView),
    # > Doctorate education
    path('supervised_propositions', views.SupervisedPropositionListView),
    # Creation tabs
    _path('', include(person_tabs)),
    path('curriculum', views.PersonCurriculumView),
    # Admission-related
    path('propositions/doctorate', views.DoctorateTrainingChoiceAPIView),
    path('propositions/doctorate/<uuid:uuid>', views.DoctoratePropositionView),
    _path('propositions/doctorate/<uuid:uuid>/', include(person_tabs)),
    path('propositions/doctorate/<uuid:uuid>/project', views.ProjectViewSet),
    path('propositions/doctorate/<uuid:uuid>/verify_project', admission.api.views.submission.VerifyDoctoralProjectView),
    path('propositions/doctorate/<uuid:uuid>/curriculum', views.DoctorateCurriculumView),
    path('propositions/doctorate/<uuid:uuid>/submit', admission.api.views.submission.SubmitDoctoralPropositionView),
    path('propositions/doctorate/<uuid:uuid>/cotutelle', views.CotutelleAPIView),
    path('propositions/doctorate/<uuid:uuid>/accounting', views.DoctorateAccountingView),
    path('propositions/doctorate/<uuid:uuid>/training_choice', views.DoctorateUpdateAdmissionTypeAPIView),
    path('propositions/doctorate/<uuid:uuid>/<str:tab>/specific-question', views.DoctorateSpecificQuestionListView),
    path('propositions/doctorate/<uuid:uuid>/pdf-recap', views.DoctoratePDFRecapView),
    path('propositions/doctorate/<uuid:uuid>/documents', views.DoctorateRequestedDocumentListView),
    # Supervision
    path('propositions/doctorate/<uuid:uuid>/supervision', views.SupervisionAPIView),
    path(
        'propositions/doctorate/<uuid:uuid>/supervision/set-reference-promoter',
        views.SupervisionSetReferencePromoterAPIView,
    ),
    path(
        'propositions/doctorate/<uuid:uuid>/supervision/submit-ca',
        views.SupervisionSubmitCaAPIView,
    ),
    path('propositions/doctorate/<uuid:uuid>/supervision/request-signatures', views.RequestSignaturesAPIView),
    path('propositions/doctorate/<uuid:uuid>/supervision/approve', views.ApprovePropositionAPIView),
    path('propositions/doctorate/<uuid:uuid>/supervision/external/<token>', views.ExternalApprovalPropositionAPIView),
    path('propositions/doctorate/<uuid:uuid>/supervision/approve-by-pdf', views.ApproveByPdfPropositionAPIView),
    # Doctorate
    path('propositions/doctorate/<uuid:uuid>/doctorate', views.DoctorateAPIView),
    # > General education
    path('propositions/general-education', views.GeneralTrainingChoiceAPIView),
    path('propositions/general-education/<uuid:uuid>', views.GeneralPropositionView),
    path('propositions/general-education/<uuid:uuid>/training-choice', views.GeneralUpdateTrainingChoiceAPIView),
    path('propositions/general-education/<uuid:uuid>/person', views.GeneralPersonView),
    path('propositions/general-education/<uuid:uuid>/coordonnees', views.GeneralCoordonneesView),
    path('propositions/general-education/<uuid:uuid>/secondary-studies', views.GeneralSecondaryStudiesView),
    path('propositions/general-education/<uuid:uuid>/specific-question', views.GeneralSpecificQuestionAPIView),
    path('propositions/general-education/<uuid:uuid>/identification', views.GeneralIdentificationView),
    path('propositions/general-education/<uuid:uuid>/curriculum', views.GeneralCurriculumView),
    path('propositions/general-education/<uuid:uuid>/pool-questions', views.PoolQuestionsView),
    path(
        'propositions/general-education/<uuid:uuid>/<str:tab>/specific-question', views.GeneralSpecificQuestionListView
    ),
    path('propositions/general-education/<uuid:uuid>/pdf-recap', views.GeneralPDFRecapView),
    path('propositions/general-education/<uuid:uuid>/accounting', views.GeneralAccountingView),
    _path('propositions/general-education/<uuid:uuid>/', include(general_education_view_set_router.urls)),
    path('propositions/general-education/<uuid:uuid>/submit', views.SubmitGeneralEducationPropositionView),
    path('propositions/general-education/<uuid:uuid>/documents', views.GeneralRequestedDocumentListView),
    path(
        'propositions/general-education/<uuid:uuid>/open-application-fees-payment',
        views.OpenApplicationFeesPaymentView,
    ),
    path(
        'propositions/general-education/<uuid:uuid>/list-application-fees',
        views.ApplicationFeesListView,
    ),
    # > Continuing education
    path('propositions/continuing-education', views.ContinuingTrainingChoiceAPIView),
    path('propositions/continuing-education/<uuid:uuid>', views.ContinuingPropositionView),
    path('propositions/continuing-education/<uuid:uuid>/training-choice', views.ContinuingUpdateTrainingChoiceAPIView),
    path('propositions/continuing-education/<uuid:uuid>/person', views.ContinuingPersonView),
    path('propositions/continuing-education/<uuid:uuid>/coordonnees', views.ContinuingCoordonneesView),
    path('propositions/continuing-education/<uuid:uuid>/secondary-studies', views.ContinuingSecondaryStudiesView),
    path('propositions/continuing-education/<uuid:uuid>/curriculum', views.ContinuingCurriculumView),
    path('propositions/continuing-education/<uuid:uuid>/specific-question', views.ContinuingSpecificQuestionAPIView),
    path(
        'propositions/continuing-education/<uuid:uuid>/<str:tab>/specific-question',
        views.ContinuingSpecificQuestionListView,
    ),
    path('propositions/continuing-education/<uuid:uuid>/pdf-recap', views.ContinuingPDFRecapView),
    _path('propositions/continuing-education/<uuid:uuid>/', include(continuing_education_view_set_router.urls)),
    path('propositions/continuing-education/<uuid:uuid>/submit', views.SubmitContinuingEducationPropositionView),
    path('continuing-education/<str:sigle>/<int:annee>', views.RetrieveContinuingEducationSpecificInformationView),
    path('propositions/continuing-education/<uuid:uuid>/documents', views.ContinuingRequestedDocumentListView),
    # Autocompletes
    path('autocomplete/sector', views.AutocompleteSectorView),
    path('autocomplete/sector/<str:sigle>/doctorates', views.AutocompleteDoctoratView),
    path('autocomplete/general-education', views.AutocompleteGeneralEducationView),
    path('autocomplete/continuing-education', views.AutocompleteContinuingEducationView),
    path('autocomplete/tutor', views.AutocompleteTutorView),
    path('autocomplete/person', views.AutocompletePersonView),
    path('autocomplete/diplomatic-post', views.AutocompleteDiplomaticPostView),
    # Others
    path('campus', views.ListCampusView),
    path('campus/<uuid:uuid>', views.RetrieveCampusView),
    path('diplomatic-post/<int:code>', views.RetrieveDiplomaticPostView),
    # Payment method
    path('candidate/<str:noma>/application_fees_payment_method', views.PaymentMethodAPIView),
]
