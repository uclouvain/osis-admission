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
from django.urls import include, path

import admission.views.autocomplete as autocomplete_views
from admission.views.config.cdd_mail_templates import *
from admission.views.doctorate.cdd import *

app_name = 'admission'

# Autocomplete
autocomplete_paths = [
    path('candidates', autocomplete_views.CandidatesAutocomplete.as_view(), name='candidates'),
    path('countries', autocomplete_views.CountriesAutocomplete.as_view(), name='countries'),
    path('promoters', autocomplete_views.PromotersAutocomplete.as_view(), name='promoters'),
]

# Doctorate
doctorate_update_paths = [
    path('person', CddDoctorateAdmissionPersonFormView.as_view(), name='person'),
    path('coordonnees', CddDoctorateAdmissionCoordonneesFormView.as_view(), name='coordonnees'),
    path('curriculum', CddDoctorateAdmissionCurriculumFormView.as_view(), name='curriculum'),
    path('education', CddDoctorateAdmissionEducationFormView.as_view(), name='education'),
    path('languages', CddDoctorateAdmissionLanguagesFormView.as_view(), name='languages'),
    path('project', CddDoctorateAdmissionProjectFormView.as_view(), name='project'),
    path('cotutelle', CddDoctorateAdmissionCotutelleFormView.as_view(), name='cotutelle'),
    path('supervision', CddDoctorateAdmissionSupervisionFormView.as_view(), name='supervision'),
    path('confirmation', CddDoctorateAdmissionConfirmationFormView.as_view(), name='confirmation'),
    path('extension-request', CddDoctorateAdmissionExtensionRequestFormView.as_view(), name='extension-request'),
]
doctorate_detail_paths = [
    path('person', CddDoctorateAdmissionPersonDetailView.as_view(), name='person'),
    path('coordonnees', CddDoctorateAdmissionCoordonneesDetailView.as_view(), name='coordonnees'),
    path('curriculum', CddDoctorateAdmissionCurriculumDetailView.as_view(), name='curriculum'),
    path('education', CddDoctorateAdmissionEducationDetailView.as_view(), name='education'),
    path('languages', CddDoctorateAdmissionLanguagesDetailView.as_view(), name='languages'),
    path('project', CddDoctorateAdmissionProjectDetailView.as_view(), name='project'),
    path('cotutelle', CddDoctorateAdmissionCotutelleDetailView.as_view(), name='cotutelle'),
    path('supervision', CddDoctorateAdmissionSupervisionDetailView.as_view(), name='supervision'),
    path('history', CddDoctorateHistoryView.as_view(), name='history'),
    path('history-all', CddDoctorateHistoryAllView.as_view(), name='history-all'),
    path('send-mail', CddDoctorateSendMailView.as_view(), name='send-mail'),
    path('confirmation', CddDoctorateAdmissionConfirmationDetailView.as_view(), name='confirmation'),
    path(
        'confirmation-success',
        CddDoctorateAdmissionConfirmationSuccessDecisionView.as_view(),
        name='confirmation-success',
    ),
    path(
        'confirmation-failure',
        CddDoctorateAdmissionConfirmationFailureDecisionView.as_view(),
        name='confirmation-failure',
    ),
    path(
        'confirmation-retaking',
        CddDoctorateAdmissionConfirmationRetakingDecisionView.as_view(),
        name='confirmation-retaking',
    ),
    path('extension-request', CddDoctorateAdmissionExtensionRequestDetailView.as_view(), name='extension-request'),
    path('update/', include((doctorate_update_paths, 'update'))),
]
doctorate_cdd_paths = [
    path('', CddDoctorateAdmissionList.as_view(), name='list'),
    path('<uuid:pk>/', include(doctorate_detail_paths)),
    path('<uuid:uuid>/history-api', CddDoctorateHistoryAPIView.as_view(), name='history-api'),
]

cdd_mail_template_paths = [
    path('', CddMailTemplateListView.as_view(), name='list'),
    path('preview/<str:identifier>/<int:pk>', CddMailTemplatePreview.as_view(), name='preview'),
    path('edit/<str:identifier>/<int:pk>', CddMailTemplateChangeView.as_view(), name='edit'),
    path('delete/<str:identifier>/<int:pk>', CddMailTemplateDeleteView.as_view(), name='delete'),
    path('add/<str:identifier>', CddMailTemplateChangeView.as_view(), name='add'),
]
config_paths = [
    path('cdd_mail_template/', include((cdd_mail_template_paths, 'cdd_mail_template'))),
]

doctorate_paths = [
    path('cdd/', include((doctorate_cdd_paths, 'cdd'))),
]
urlpatterns = [
    # Doctorate admissions
    path('doctorate/', include((doctorate_paths, 'doctorate'))),
    # Configuration
    path('config/', include((config_paths, 'config'))),
    # Autocomplete
    path('autocomplete/', include((autocomplete_paths, 'autocomplete'))),
]
