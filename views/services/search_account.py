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
from typing import List

from django.contrib.messages import SUCCESS
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import FormView

__all__ = [
    "SearchAccountView"
]

from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.commands import InitialiserPropositionFusionPersonneCommand
from admission.forms.admission.person_merge_proposal_form import PersonMergeProposalForm
from base.models.person import Person
from base.views.common import display_success_messages
from infrastructure.messages_bus import message_bus_instance
from osis_common.utils.htmx import HtmxMixin


class SearchAccountView(HtmxMixin, FormView):

    name = "search_account"

    template_name = "admission/modal_search_account.html"
    htmx_template_name = "admission/modal_search_account.html"
    urlpatterns = {'search-account-modal': 'search-account-modal/<uuid:uuid>'}

    form_class = PersonMergeProposalForm

    @property
    def candidate(self):
        admission = BaseAdmission.objects.get(uuid=self.kwargs['uuid'])
        return Person.objects.values(
            'first_name', 'middle_name', 'last_name', 'email', 'gender', 'birth_date', 'civil_state',
            'birth_place', 'country_of_citizenship__name', 'national_number', 'id_card_number',
            'passport_number', 'last_registration_id', 'global_id',
        ).get(pk=admission.candidate_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['candidate'] = self.candidate
        search_context = self.request.session.get('search_context', {})
        context.update(**search_context)
        return context

    def form_valid(self, form):
        display_success_messages(self.request, messages_to_display="La proposition de fusion a été créée avec succès")
        message_bus_instance.invoke(
            InitialiserPropositionFusionPersonneCommand(
                original_global_id=self.candidate['global_id'],
                nom=form.cleaned_data['last_name'],
                prenom=form.cleaned_data['first_name'],
                autres_prenoms=form.cleaned_data['middle_name'],
                date_naissance=form.cleaned_data['birth_date'],
                lieu_naissance=form.cleaned_data['birth_place'],
                email=form.cleaned_data['email'],
                genre=form.cleaned_data['gender'],
                nationalite=form.cleaned_data['country_of_citizenship'],
                etat_civil=form.cleaned_data['civil_state'],
                numero_national=form.cleaned_data['national_number'],
                numero_carte_id=form.cleaned_data['id_card_number'],
                numero_passeport=form.cleaned_data['passport_number'],
                dernier_noma_connu=form.cleaned_data['last_registration_id'],
            )
        )
        return HttpResponse(status=200, headers={'HX-Refresh': 'true'})

    def form_invalid(self, form):
        response = super().form_invalid(form)
        response.status_code = 200  # invalid request
        return response

    def get_success_url(self):
        return reverse(
            'admission:general-education:checklist',
            kwargs={'uuid': self.kwargs['uuid']}
        ) + "#donnees_personnelles"
