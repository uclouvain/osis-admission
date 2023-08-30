# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.forms import model_to_dict
from django.views.generic import TemplateView

__all__ = [
    "SearchAccountView"
]

from admission.contrib.models.base import BaseAdmission
from base.models.person import Person


class SearchAccountView(TemplateView):

    template_name = "admission/modal_search_account.html"
    urlpatterns = {'search-account-modal': 'search-account-modal/<uuid:uuid>'}

    @property
    def candidate(self):
        admission = BaseAdmission.objects.get(uuid=self.kwargs['uuid'])
        return Person.objects.values(
            'first_name', 'middle_name', 'last_name', 'email', 'gender', 'birth_date', 'civil_state',
            'birth_place', 'country_of_citizenship__name', 'national_number', 'id_card_number', 'passport_number',
            'last_registration_id',
        ).get(pk=admission.candidate_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['candidate'] = self.candidate
        search_context = self.request.session.get('search_context', {})
        context.update(**search_context)
        return context
