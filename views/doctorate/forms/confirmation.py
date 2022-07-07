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
from django.utils.translation import gettext as _
from django.views.generic import FormView

from admission.ddd.projet_doctoral.doctorat.commands import RecupererDoctoratQuery
from admission.ddd.projet_doctoral.doctorat.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.commands import (
    ModifierEpreuveConfirmationParCDDCommand,
    RecupererDerniereEpreuveConfirmationQuery,
    TeleverserAvisRenouvellementMandatRechercheCommand,
)
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonTrouveeException,
)
from admission.forms.doctorate.confirmation import ConfirmationForm, ConfirmationOpinionForm
from admission.utils import get_cached_admission_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import PermissionRequiredMixin


class DoctorateAdmissionLastConfirmationMixin(LoginRequiredMixin, PermissionRequiredMixin):
    @cached_property
    def admission(self):
        return get_cached_admission_perm_obj(self.kwargs['pk'])

    def get_permission_object(self):
        return self.admission

    @cached_property
    def last_confirmation_paper(self) -> EpreuveConfirmationDTO:
        try:
            last_confirmation_paper = message_bus_instance.invoke(
                RecupererDerniereEpreuveConfirmationQuery(self.kwargs.get('pk'))
            )
            if not last_confirmation_paper:
                raise Http404(_('Confirmation paper not found.'))
            return last_confirmation_paper
        except (DoctoratNonTrouveException, EpreuveConfirmationNonTrouveeException) as e:
            raise Http404(e.message)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}

        try:
            context['doctorate'] = message_bus_instance.invoke(
                RecupererDoctoratQuery(self.kwargs.get('pk')),
            )
        except DoctoratNonTrouveException as e:
            raise Http404(e.message)

        context['confirmation_paper'] = self.last_confirmation_paper

        return context


class DoctorateAdmissionConfirmationFormView(DoctorateAdmissionLastConfirmationMixin, FormView):
    template_name = 'admission/doctorate/forms/confirmation.html'
    form_class = ConfirmationForm
    permission_required = 'admission.change_doctorateadmission_confirmation'

    def get_initial(self):
        return {
            'date_limite': self.last_confirmation_paper.date_limite,
            'date': self.last_confirmation_paper.date,
            'rapport_recherche': self.last_confirmation_paper.rapport_recherche,
            'proces_verbal_ca': self.last_confirmation_paper.proces_verbal_ca,
            'avis_renouvellement_mandat_recherche': self.last_confirmation_paper.avis_renouvellement_mandat_recherche,
        }

    def form_valid(self, form):
        # Save the confirmation paper
        message_bus_instance.invoke(
            ModifierEpreuveConfirmationParCDDCommand(
                uuid=self.last_confirmation_paper.uuid,
                **form.cleaned_data,
            )
        )

        return super().form_valid(form=form)

    def get_success_url(self):
        return reverse('admission:doctorate:confirmation', args=[self.kwargs.get('pk')])


class DoctorateAdmissionConfirmationOpinionFormView(DoctorateAdmissionLastConfirmationMixin, FormView):
    template_name = 'admission/doctorate/forms/confirmation_opinion.html'
    form_class = ConfirmationOpinionForm
    permission_required = 'admission.upload_pdf_confirmation'

    def get_initial(self):
        return {
            'avis_renouvellement_mandat_recherche': self.last_confirmation_paper.avis_renouvellement_mandat_recherche,
        }

    def form_valid(self, form):
        # Save the confirmation paper
        message_bus_instance.invoke(
            TeleverserAvisRenouvellementMandatRechercheCommand(
                uuid=self.last_confirmation_paper.uuid,
                **form.cleaned_data,
            )
        )

        return super().form_valid(form=form)

    def get_success_url(self):
        return reverse('admission:doctorate:confirmation', args=[self.kwargs.get('pk')])
