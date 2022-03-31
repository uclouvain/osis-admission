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
from admission.views.doctorate.cdd import *

app_name = 'admission'

# Autocomplete
autocomplete_paths = [
    path('candidates', autocomplete_views.CandidatesAutocomplete.as_view(), name='candidates'),
    path('countries', autocomplete_views.CountriesAutocomplete.as_view(), name='countries'),
    path('promoters', autocomplete_views.PromotersAutocomplete.as_view(), name='promoters'),
]

# Doctorate
doctorate_cdd_paths = [
    path('', CddDoctorateAdmissionList.as_view(), name='list'),
    path('<uuid:pk>/', include([
        path('person', CddDoctorateAdmissionPersonDetailView.as_view(), name='person'),
        path('coordonnees', CddDoctorateAdmissionCoordonneesDetailView.as_view(), name='coordonnees'),
        path('curriculum', CddDoctorateAdmissionCurriculumDetailView.as_view(), name='curriculum'),
        path('education', CddDoctorateAdmissionEducationDetailView.as_view(), name='education'),
        path('languages', CddDoctorateAdmissionLanguagesDetailView.as_view(), name='languages'),
        path('project', CddDoctorateAdmissionProjectDetailView.as_view(), name='project'),
        path('cotutelle', CddDoctorateAdmissionCotutelleDetailView.as_view(), name='cotutelle'),
        path('supervision', CddDoctorateAdmissionSupervisionDetailView.as_view(), name='supervision'),
        path('update/', include(([
            path('person', CddDoctorateAdmissionPersonFormView.as_view(), name='person'),
            path('coordonnees', CddDoctorateAdmissionCoordonneesFormView.as_view(), name='coordonnees'),
            path('curriculum', CddDoctorateAdmissionCurriculumFormView.as_view(), name='curriculum'),
            path('education', CddDoctorateAdmissionEducationFormView.as_view(), name='education'),
            path('languages', CddDoctorateAdmissionLanguagesFormView.as_view(), name='languages'),
            path('project', CddDoctorateAdmissionProjectFormView.as_view(), name='project'),
            path('cotutelle', CddDoctorateAdmissionCotutelleFormView.as_view(), name='cotutelle'),
            path('supervision', CddDoctorateAdmissionSupervisionFormView.as_view(), name='supervision'),
        ], 'update'))),
    ])),
]

urlpatterns = [
    # Doctorate admissions
    path('doctorate/', include(([
        path('cdd/', include((doctorate_cdd_paths, 'cdd'))),
    ], 'doctorate'))),
    # Autocomplete
    path('autocomplete/', include((autocomplete_paths, 'autocomplete'))),
]
