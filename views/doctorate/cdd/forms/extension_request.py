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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import FormView

from admission.auth.mixins import CddRequiredMixin
from admission.ddd.projet_doctoral.doctorat.commands import RecupererDoctoratQuery
from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.projet_doctoral.doctorat.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.commands import (
    RecupererDerniereEpreuveConfirmationQuery,
    SoumettreAvisProlongationCommand,
)
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonTrouveeException,
)
from admission.forms.doctorate.cdd.extension_request import ExtensionRequestForm
from admission.views.mixins.business_exceptions_form_view_mixin import BusinessExceptionFormViewMixin
from infrastructure.messages_bus import message_bus_instance


class CddDoctorateAdmissionExtensionRequestFormView(
    LoginRequiredMixin,
    CddRequiredMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    template_name = 'admission/doctorate/cdd/forms/extension_request.html'
    form_class = ExtensionRequestForm

    @cached_property
    def last_confirmation_paper(self) -> EpreuveConfirmationDTO:
        try:
            return message_bus_instance.invoke(RecupererDerniereEpreuveConfirmationQuery(self.kwargs.get('pk')))
        except (DoctoratNonTrouveException, EpreuveConfirmationNonTrouveeException) as e:
            raise Http404(e.message)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            context['doctorate'] = message_bus_instance.invoke(
                RecupererDoctoratQuery(self.kwargs.get('pk')),
            )
        except DoctoratNonTrouveException as e:
            raise Http404(e.message)

        return context

    def get_initial(self):
        return (
            {
                'avis_cdd': self.last_confirmation_paper.demande_prolongation.avis_cdd,
            }
            if self.last_confirmation_paper.demande_prolongation
            else {}
        )

    def call_command(self, form):
        message_bus_instance.invoke(
            SoumettreAvisProlongationCommand(
                uuid=self.last_confirmation_paper.uuid,
                **form.cleaned_data,
            )
        )

    def get_success_url(self):
        return reverse('admission:doctorate:cdd:extension-request', args=[self.kwargs.get('pk')])
