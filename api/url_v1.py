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
from django.urls import path as _path

from admission.api import views


def path(pattern, view, name=None):
    return _path(pattern, view.as_view(), name=getattr(view, 'name', name))


app_name = "admission_api_v1"
urlpatterns = [
    path('person', views.PersonViewSet),
    path('coordonnees', views.CoordonneesViewSet),
    path('propositions', views.PropositionListView),
    path('secondary_studies', views.SecondaryStudiesViewSet),
    path('languages_knowledge', views.LanguagesKnowledgeViewSet),
    path('propositions/<uuid:uuid>', views.PropositionViewSet),
    path('propositions/<uuid:uuid>/verify', views.VerifyPropositionView),
    path('propositions/<uuid:uuid>/cotutelle', views.CotutelleAPIView),
    path('propositions/<uuid:uuid>/supervision', views.SupervisionAPIView),
    path('propositions/<uuid:uuid>/request_signatures', views.RequestSignaturesAPIView),
    path('autocomplete/sector', views.AutocompleteSectorView),
    path('autocomplete/sector/<str:sigle>/doctorates', views.AutocompleteDoctoratView),
    path('autocomplete/tutor', views.AutocompleteTutorView),
    path('autocomplete/person', views.AutocompletePersonView),
]
