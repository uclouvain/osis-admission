# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.urls import reverse
from django.views.generic import FormView

from admission.ddd.admission.enums import FORMATTED_RELATIONSHIPS, LienParente
from admission.ddd.admission.formation_generale.commands import CompleterComptabilitePropositionCommand
from admission.forms.admission.accounting import AccountingForm
from admission.views.common.detail_tabs.accounting import AccountingMixinView
from infrastructure.messages_bus import message_bus_instance

__all__ = ['AccountingFormView']


class AccountingFormView(AccountingMixinView, FormView):
    template_name = 'admission/forms/accounting.html'
    permission_required = 'admission.view_admission_accounting'
    urlpatterns = 'accounting'
    update_requested_documents = True
    update_admission_author = True
    form_class = AccountingForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['relationships'] = {elt.name: elt.value for elt in LienParente}
        context_data['formatted_relationships'] = FORMATTED_RELATIONSHIPS
        return context_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_general_admission'] = self.is_general
        kwargs['with_assimilation'] = self.with_assimilation
        kwargs['last_french_community_high_education_institutes_attended'] = self.accounting[
            'derniers_etablissements_superieurs_communaute_fr_frequentes'
        ]

        if self.is_general and self.proposition.formation.campus:
            kwargs['education_site'] = self.proposition.formation.campus.nom

        return kwargs

    def get_initial(self):
        return self.accounting

    def form_valid(self, form):
        message_bus_instance.invoke(
            CompleterComptabilitePropositionCommand(
                uuid_proposition=self.admission_uuid,
                **form.cleaned_data,
            )
        )
        return super().form_valid(form)

    def get_success_url(self):
        return self.next_url or reverse(f'admission:{self.current_context}:accounting', kwargs=self.kwargs)
