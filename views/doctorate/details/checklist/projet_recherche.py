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
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, FormView

from admission.ddd.admission.doctorat.preparation.commands import (
    ModifierChecklistChoixFormationCommand, DemanderCandidatModificationCACommand,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import DoctoratNonTrouveException
from admission.forms.admission.checklist import (
    ChoixFormationForm,
)
from admission.utils import add_messages_into_htmx_response
from admission.views.common.mixins import LoadDossierViewMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    'ProjetRechercheDemanderModificationCAView',
]


__namespace__ = False


class ProjetRechercheDemanderModificationCAView(
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    urlpatterns = 'projet-recherche-demand-modification-ca'
    permission_required = 'admission.change_admission_supervision'
    template_name = 'admission/doctorate/includes/checklist/projet_recherche_demander_modification.html'
    htmx_template_name = (
        'admission/doctorate/includes/checklist/projet_recherche_demander_modification.html'
    )

    def get_form(self, form_class=None):
        return self.financability_dispensation_notification_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                NotifierCandidatDerogationFinancabiliteCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    objet_message=form.cleaned_data['subject'],
                    corps_message=form.cleaned_data['body'],
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                form.add_error(None, exception.message)
            return self.form_invalid(form)

        return super().form_valid(form)
