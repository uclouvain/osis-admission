# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.api.views.accounting import (
    DoctorateAccountingView,
    GeneralAccountingView,
)
from admission.api.views.approvals import *
from admission.api.views.autocomplete import *
from admission.api.views.continuing_education import (
    RetrieveContinuingEducationSpecificInformationView,
)
from admission.api.views.coordonnees import (
    ContinuingCoordonneesView,
    CoordonneesViewSet,
    GeneralCoordonneesView,
)
from admission.api.views.cotutelle import CotutelleAPIView
from admission.api.views.curriculum import *
from admission.api.views.dashboard import DashboardViewSet
from admission.api.views.doctorate import DoctorateAPIView
from admission.api.views.documents import (
    ContinuingRequestedDocumentListView,
    DoctorateRequestedDocumentListView,
    GeneralRequestedDocumentListView,
)
from admission.api.views.languages_knowledge import LanguagesKnowledgeViewSet
from admission.api.views.payment import (
    ApplicationFeesListView,
    OpenApplicationFeesPaymentView,
)
from admission.api.views.payment_method import PaymentMethodAPIView
from admission.api.views.pdf_recap import (
    ContinuingPDFRecapView,
    DoctoratePDFRecapView,
    GeneralPDFRecapView,
)
from admission.api.views.person import (
    ContinuingPersonView,
    GeneralPersonView,
    IdentificationDTOView,
    PersonViewSet,
)
from admission.api.views.pool_questions import PoolQuestionsView
from admission.api.views.project import *
from admission.api.views.proposition import (
    ContinuingPropositionView,
    DoctoratePropositionView,
    GeneralPropositionView,
)
from admission.api.views.references import (
    ListCampusView,
    RetrieveCampusView,
    RetrieveDiplomaticPostView,
)
from admission.api.views.secondary_studies import (
    ContinuingSecondaryStudiesView,
    GeneralSecondaryStudiesView,
    SecondaryStudiesViewSet,
)
from admission.api.views.signatures import RequestSignaturesAPIView
from admission.api.views.specific_questions import (
    ContinuingSpecificQuestionAPIView,
    ContinuingSpecificQuestionListView,
    DoctorateSpecificQuestionListView,
    GeneralIdentificationView,
    GeneralSpecificQuestionAPIView,
    GeneralSpecificQuestionListView,
)
from admission.api.views.submission import *
from admission.api.views.supervision import *
from admission.api.views.training_choice import (
    ContinuingTrainingChoiceAPIView,
    ContinuingUpdateTrainingChoiceAPIView,
    DoctorateTrainingChoiceAPIView,
    DoctorateUpdateAdmissionTypeAPIView,
    GeneralTrainingChoiceAPIView,
    GeneralUpdateTrainingChoiceAPIView,
)
