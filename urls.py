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
from admission.views.config.cdd_config import *
from admission.views.config.cdd_mail_templates import *
from admission.views.doctorate import *
from admission.views.doctorate.cdd import *

app_name = 'admission'

# Autocomplete
autocomplete_paths = [
    path('candidates', autocomplete_views.CandidatesAutocomplete.as_view(), name='candidates'),
    path('countries', autocomplete_views.CountriesAutocomplete.as_view(), name='countries'),
    path('promoters', autocomplete_views.PromotersAutocomplete.as_view(), name='promoters'),
]

# Doctorate
confirmation_tabs = [
    path('opinion', DoctorateAdmissionConfirmationOpinionFormView.as_view(), name='opinion'),
    path('success', DoctorateAdmissionConfirmationSuccessDecisionView.as_view(), name='success'),
    path('failure', DoctorateAdmissionConfirmationFailureDecisionView.as_view(), name='failure'),
    path('retaking', DoctorateAdmissionConfirmationRetakingDecisionView.as_view(), name='retaking'),
]
doctorate_update_paths = [
    path('person', DoctorateAdmissionPersonFormView.as_view(), name='person'),
    path('coordonnees', DoctorateAdmissionCoordonneesFormView.as_view(), name='coordonnees'),
    path('curriculum', DoctorateAdmissionCurriculumFormView.as_view(), name='curriculum'),
    path('education', DoctorateAdmissionEducationFormView.as_view(), name='education'),
    path('languages', DoctorateAdmissionLanguagesFormView.as_view(), name='languages'),
    path('project', DoctorateAdmissionProjectFormView.as_view(), name='project'),
    path('cotutelle', DoctorateAdmissionCotutelleFormView.as_view(), name='cotutelle'),
    path('supervision', DoctorateAdmissionSupervisionFormView.as_view(), name='supervision'),
    path('confirmation', DoctorateAdmissionConfirmationFormView.as_view(), name='confirmation'),
    path('extension-request', DoctorateAdmissionExtensionRequestFormView.as_view(), name='extension-request'),
]
doctorate_training_paths = [
    path('add/<str:category>', DoctorateTrainingActivityAddView.as_view(), name='add'),
    path('edit/<uuid:activity_id>', DoctorateTrainingActivityEditView.as_view(), name='edit'),
    path('delete/<uuid:activity_id>', DoctorateTrainingActivityDeleteView.as_view(), name='delete'),
]
doctorate_detail_paths = [
    path('person', DoctorateAdmissionPersonDetailView.as_view(), name='person'),
    path('coordonnees', DoctorateAdmissionCoordonneesDetailView.as_view(), name='coordonnees'),
    path('curriculum', DoctorateAdmissionCurriculumDetailView.as_view(), name='curriculum'),
    path('education', DoctorateAdmissionEducationDetailView.as_view(), name='education'),
    path('languages', DoctorateAdmissionLanguagesDetailView.as_view(), name='languages'),
    path('project', DoctorateAdmissionProjectDetailView.as_view(), name='project'),
    path('cotutelle', DoctorateAdmissionCotutelleDetailView.as_view(), name='cotutelle'),
    path('supervision', DoctorateAdmissionSupervisionDetailView.as_view(), name='supervision'),
    path('history', DoctorateHistoryView.as_view(), name='history'),
    path('history-all', DoctorateHistoryAllView.as_view(), name='history-all'),
    path('send-mail', DoctorateSendMailView.as_view(), name='send-mail'),
    path('confirmation', DoctorateAdmissionConfirmationDetailView.as_view(), name='confirmation'),
    path('confirmation/', include((confirmation_tabs, 'confirmation'))),
    path('extension-request', DoctorateAdmissionExtensionRequestDetailView.as_view(), name='extension-request'),
    path(
        'confirmation-canvas',
        DoctorateAdmissionConfirmationCanvasExportView.as_view(),
        name='confirmation-canvas',
    ),
    path('update/', include((doctorate_update_paths, 'update'))),
    path('training', DoctorateTrainingActivityView.as_view(), name='training'),
    path('training/', include((doctorate_training_paths, 'training'))),
]

doctorate_cdd_paths = [
    path('', CddDoctorateAdmissionList.as_view(), name='list'),
]

doctorate_paths = [
    # Common
    path('<uuid:pk>/', include(doctorate_detail_paths)),
    path('<uuid:uuid>/history-api', DoctorateHistoryAPIView.as_view(), name='history-api'),
    # Specific
    path('cdd/', include((doctorate_cdd_paths, 'cdd'))),
]

cdd_mail_template_paths = [
    path('', CddMailTemplateListView.as_view(), name='list'),
    path('preview/<str:identifier>/<int:pk>', CddMailTemplatePreview.as_view(), name='preview'),
    path('edit/<str:identifier>/<int:pk>', CddMailTemplateChangeView.as_view(), name='edit'),
    path('delete/<str:identifier>/<int:pk>', CddMailTemplateDeleteView.as_view(), name='delete'),
    path('add/<str:identifier>', CddMailTemplateChangeView.as_view(), name='add'),
]

cdd_config_paths = [
    path('', CddConfigListView.as_view(), name='list'),
    path('edit/<int:pk>', CddConfigChangeView.as_view(), name='edit'),
]

# Global
config_paths = [
    path('cdd_mail_template/', include((cdd_mail_template_paths, 'cdd_mail_template'))),
    path('cdd/', include((cdd_config_paths, 'cdd_config'))),
]

urlpatterns = [
    # Doctorate admissions
    path('doctorate/', include((doctorate_paths, 'doctorate'))),
    # Configuration
    path('config/', include((config_paths, 'config'))),
    # Autocomplete
    path('autocomplete/', include((autocomplete_paths, 'autocomplete'))),
]
