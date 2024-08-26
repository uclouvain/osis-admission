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
import re

import waffle
from django.core.exceptions import PermissionDenied
from django.forms import model_to_dict
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import FormView

__all__ = [
    "SearchAccountView",
]

from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.commands import InitialiserPropositionFusionPersonneCommand
from admission.forms.admission.person_merge_proposal_form import PersonMergeProposalForm
from admission.templatetags.admission import format_matricule
from admission.utils import get_cached_general_education_admission_perm_obj
from base.models.person import Person
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from base.utils.htmx import HtmxPermissionRequiredMixin
from base.views.common import display_success_messages
from osis_common.utils.htmx import HtmxMixin


class SearchAccountView(HtmxMixin, HtmxPermissionRequiredMixin, FormView):

    name = "search_account"

    template_name = "admission/modal_search_account.html"
    htmx_template_name = "admission/modal_search_account.html"
    urlpatterns = {'search-account-modal': 'search-account-modal/<uuid:uuid>'}
    permission_required = "admission.merge_candidate_with_known_person"

    form_class = PersonMergeProposalForm

    @property
    def admission(self):
        return BaseAdmission.objects.get(uuid=self.kwargs['uuid'])

    @property
    def candidate(self):
        return Person.objects.values(
            'first_name', 'middle_name', 'last_name', 'national_number', 'gender', 'birth_date',
            'email', 'civil_state', 'birth_place', 'country_of_citizenship__name', 'id_card_number',
            'passport_number', 'id_card_expiry_date', 'passport_expiry_date', 'global_id'
        ).get(baseadmissions__uuid=self.kwargs['uuid'])

    @property
    def proposal_merge(self):
        try:
            return PersonMergeProposal.objects.get(original_person__global_id=self.candidate['global_id'])
        except PersonMergeProposal.DoesNotExist:
            return None

    @property
    def merge_person(self):
        return self.proposal_merge.proposal_merge_person if self.proposal_merge else None

    def get_initial(self):
        return model_to_dict(self.merge_person) \
            if self.proposal_merge and self.proposal_merge.status == PersonMergeStatus.PENDING.name else {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['uuid'] = self.kwargs['uuid']
        context['candidate'] = self.candidate
        context['merge_person'] = self.proposal_merge
        context['peut_refuser_fusion'] = self.peut_refuser_fusion()
        search_context = self.request.session.get('search_context', {})
        context.update(**search_context)
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        is_required = request.POST.get('action') == 'MERGE'

        if not is_required:
            form.is_valid()
            return self.form_valid(form)
        elif waffle.switch_is_active('admission:allow-merge-with-existing-account'):
            return super().post(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def form_valid(self, form):
        from infrastructure.messages_bus import message_bus_instance
        display_success_messages(self.request, messages_to_display="La proposition de fusion a été créée avec succès")
        message_bus_instance.invoke(
            InitialiserPropositionFusionPersonneCommand(
                existing_merge_person_id=self.merge_person.id if self.merge_person else None,
                status=self.request.POST.get('action'),
                original_global_id=self.candidate['global_id'],
                selected_global_id=format_matricule(self.request.POST.get('global_id')),
                nom=form.cleaned_data.get('last_name', ''),
                prenom=form.cleaned_data.get('first_name', ''),
                autres_prenoms=form.cleaned_data.get('middle_name', ''),
                date_naissance=form.cleaned_data.get('birth_date'),
                lieu_naissance=form.cleaned_data.get('birth_place', ''),
                email=form.cleaned_data.get('email', ''),
                genre=form.cleaned_data.get('gender', ''),
                sex=form.cleaned_data.get('gender', ''),  # TODO: Clarify sex/gender notion with DigIT
                nationalite=form.cleaned_data.get('country_of_citizenship', ''),
                etat_civil=form.cleaned_data.get('civil_state', ''),
                numero_national=form.cleaned_data.get('national_number', ''),
                numero_carte_id=form.cleaned_data.get('id_card_number', ''),
                numero_passeport=form.cleaned_data.get('passport_number', ''),
                dernier_noma_connu=form.cleaned_data.get('last_registration_id', ''),
                expiration_carte_id=form._to_YYYYMMDD(self.request.POST.get('id_card_expiry_date')),
                expiration_passeport=form._to_YYYYMMDD(self.request.POST.get('passport_expiry_date')),
                educational_curex_uuids=self.get_educational_curex_form_values(),
                professional_curex_uuids=self.get_professional_curex_form_values(),
                annee_diplome_etudes_secondaires=self.get_high_school_graduation_year(),
            )
        )
        return HttpResponse(status=200, headers={'HX-Refresh': 'true'})

    def form_invalid(self, form):
        response = super().form_invalid(form)
        response.status_code = 200  # invalid request
        return response

    def get_professional_curex_form_values(self):
        return self.request.POST.getlist('professional')

    def get_educational_curex_form_values(self):
        return self.request.POST.getlist('educational')

    def get_high_school_graduation_year(self):
        return self.request.POST.getlist('high_school_graduation_year')

    def get_success_url(self):
        return reverse(
            'admission:general-education:checklist',
            kwargs={'uuid': self.kwargs['uuid']}
        ) + "#donnees_personnelles"

    def peut_refuser_fusion(self):
        # pas le temps pour faire ça en DDD
        candidate = self.candidate
        digit_results = self.proposal_merge.similarity_result
        for result in digit_results:
            # ne peut pas refuser fusion si NISS identiques
            if result['person']['nationalRegister'] and candidate['national_number'] and (
                    result['person']['nationalRegister'] == _only_digits(candidate['national_number'])
            ):
                return False
        return True

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])


def _only_digits(input_string):
    return re.sub('[^0-9]', '', input_string)
