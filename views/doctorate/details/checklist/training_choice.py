# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView

from admission.ddd.admission.doctorat.preparation.commands import (
    ModifierChecklistChoixFormationCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    DoctoratNonTrouveException,
)
from admission.forms.admission.doctorate.checklist import ChoixFormationForm
from admission.views.common.mixins import LoadDossierViewMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    'ChoixFormationFormView',
    'ChoixFormationDetailView',
]


__namespace__ = False


class ChoixFormationFormView(LoadDossierViewMixin, FormView):
    urlpatterns = 'choix-formation-update'
    permission_required = 'admission.checklist_change_training_choice'
    template_name = 'admission/doctorate/includes/checklist/choix_formation_form.html'
    form_class = ChoixFormationForm

    def dispatch(self, request, *args, **kwargs):
        if not request.htmx:
            return redirect(
                reverse('admission:doctorate:checklist', kwargs={'uuid': self.admission_uuid}) + '#choix_formation'
            )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['training'] = self.proposition.formation
        return kwargs

    def get_initial(self):
        return {
            'type_demande': self.proposition.type,
            'annee_academique': self.proposition.annee_calculee,
            'commission_proximite': self.proposition.commission_proximite,
        }

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                ModifierChecklistChoixFormationCommand(
                    uuid_proposition=str(self.kwargs['uuid']),
                    gestionnaire=self.request.user.person.global_id,
                    type_demande=form.cleaned_data['type_demande'],
                    annee_formation=form.cleaned_data['annee_academique'],
                    commission_proximite=form.cleaned_data['commission_proximite'],
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                form.add_error(None, exception.message)
            return self.form_invalid(form)
        except DoctoratNonTrouveException:
            form.add_error('annee_academique', _('No training found for the specific year.'))
            return self.form_invalid(form)
        return HttpResponse(headers={'HX-Refresh': 'true'})


class ChoixFormationDetailView(LoadDossierViewMixin, TemplateView):
    urlpatterns = 'choix-formation-detail'
    permission_required = 'admission.checklist_change_training_choice'
    template_name = 'admission/doctorate/includes/checklist/choix_formation_detail.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.htmx:
            return redirect(
                reverse('admission:doctorate:checklist', kwargs={'uuid': self.admission_uuid}) + '#choix_formation'
            )
        return super().dispatch(request, *args, **kwargs)
