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
from .details.confirmation import DoctorateAdmissionConfirmationDetailView
from .details.coordonnees import DoctorateAdmissionCoordonneesDetailView
from .details.cotutelle import DoctorateAdmissionCotutelleDetailView
from .details.curriculum import DoctorateAdmissionCurriculumDetailView
from .details.education import DoctorateAdmissionEducationDetailView
from .details.extension_request import DoctorateAdmissionExtensionRequestDetailView
from .details.history import DoctorateHistoryAPIView, DoctorateHistoryAllView, DoctorateHistoryView
from .details.languages import DoctorateAdmissionLanguagesDetailView
from .details.person import DoctorateAdmissionPersonDetailView
from .details.project import DoctorateAdmissionProjectDetailView
from .details.supervision import DoctorateAdmissionSupervisionDetailView
from .forms.confirmation import DoctorateAdmissionConfirmationFormView, DoctorateAdmissionConfirmationOpinionFormView
from .forms.confirmation_decision import (
    DoctorateAdmissionConfirmationSuccessDecisionView,
    DoctorateAdmissionConfirmationFailureDecisionView,
    DoctorateAdmissionConfirmationRetakingDecisionView,
)
from .forms.coordonnees import DoctorateAdmissionCoordonneesFormView
from .forms.cotutelle import DoctorateAdmissionCotutelleFormView
from .forms.curriculum import DoctorateAdmissionCurriculumFormView
from .forms.education import DoctorateAdmissionEducationFormView
from .forms.extension_request import DoctorateAdmissionExtensionRequestFormView
from .forms.languages import DoctorateAdmissionLanguagesFormView
from .forms.person import DoctorateAdmissionPersonFormView
from .forms.project import DoctorateAdmissionProjectFormView
from .forms.send_mail import DoctorateSendMailView
from .forms.supervision import DoctorateAdmissionSupervisionFormView

__all__ = [
    # Details
    'DoctorateAdmissionConfirmationDetailView',
    'DoctorateAdmissionPersonDetailView',
    'DoctorateAdmissionCoordonneesDetailView',
    'DoctorateAdmissionCurriculumDetailView',
    'DoctorateAdmissionEducationDetailView',
    'DoctorateAdmissionExtensionRequestDetailView',
    'DoctorateAdmissionLanguagesDetailView',
    'DoctorateAdmissionProjectDetailView',
    'DoctorateAdmissionCotutelleDetailView',
    'DoctorateAdmissionSupervisionDetailView',
    # Forms
    'DoctorateAdmissionConfirmationFormView',
    'DoctorateAdmissionConfirmationOpinionFormView',
    'DoctorateAdmissionPersonFormView',
    'DoctorateAdmissionCoordonneesFormView',
    'DoctorateAdmissionCurriculumFormView',
    'DoctorateAdmissionEducationFormView',
    'DoctorateAdmissionExtensionRequestFormView',
    'DoctorateAdmissionLanguagesFormView',
    'DoctorateAdmissionProjectFormView',
    'DoctorateAdmissionCotutelleFormView',
    'DoctorateAdmissionSupervisionFormView',
    # Others
    'DoctorateHistoryAPIView',
    'DoctorateHistoryView',
    'DoctorateHistoryAllView',
    'DoctorateSendMailView',
    'DoctorateAdmissionConfirmationSuccessDecisionView',
    'DoctorateAdmissionConfirmationFailureDecisionView',
    'DoctorateAdmissionConfirmationRetakingDecisionView',
]
