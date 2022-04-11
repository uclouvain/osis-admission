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
from .details.coordonnees import CddDoctorateAdmissionCoordonneesDetailView
from .details.cotutelle import CddDoctorateAdmissionCotutelleDetailView
from .details.curriculum import CddDoctorateAdmissionCurriculumDetailView
from .details.education import CddDoctorateAdmissionEducationDetailView
from .details.history import CddDoctorateHistoryAPIView, CddDoctorateHistoryView
from .details.languages import CddDoctorateAdmissionLanguagesDetailView
from .details.person import CddDoctorateAdmissionPersonDetailView
from .details.project import CddDoctorateAdmissionProjectDetailView
from .details.supervision import CddDoctorateAdmissionSupervisionDetailView
from .forms.coordonnees import CddDoctorateAdmissionCoordonneesFormView
from .forms.cotutelle import CddDoctorateAdmissionCotutelleFormView
from .forms.curriculum import CddDoctorateAdmissionCurriculumFormView
from .forms.education import CddDoctorateAdmissionEducationFormView
from .forms.languages import CddDoctorateAdmissionLanguagesFormView
from .forms.person import CddDoctorateAdmissionPersonFormView
from .forms.project import CddDoctorateAdmissionProjectFormView
from .forms.supervision import CddDoctorateAdmissionSupervisionFormView
from .list import CddDoctorateAdmissionList

__all__ = [
    'CddDoctorateAdmissionList',
    'CddDoctorateAdmissionPersonDetailView',
    'CddDoctorateAdmissionCoordonneesDetailView',
    'CddDoctorateAdmissionCurriculumDetailView',
    'CddDoctorateAdmissionEducationDetailView',
    'CddDoctorateAdmissionLanguagesDetailView',
    'CddDoctorateAdmissionProjectDetailView',
    'CddDoctorateAdmissionCotutelleDetailView',
    'CddDoctorateAdmissionSupervisionDetailView',
    'CddDoctorateAdmissionPersonFormView',
    'CddDoctorateAdmissionCoordonneesFormView',
    'CddDoctorateAdmissionCurriculumFormView',
    'CddDoctorateAdmissionEducationFormView',
    'CddDoctorateAdmissionLanguagesFormView',
    'CddDoctorateAdmissionProjectFormView',
    'CddDoctorateAdmissionCotutelleFormView',
    'CddDoctorateAdmissionSupervisionFormView',
    'CddDoctorateHistoryAPIView',
    'CddDoctorateHistoryView',
]
