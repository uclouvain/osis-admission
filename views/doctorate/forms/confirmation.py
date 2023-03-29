# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.parcours_doctoral.epreuve_confirmation.commands import (
    ModifierEpreuveConfirmationParCDDCommand,
)
from admission.forms.doctorate.confirmation import ConfirmationForm
from admission.views.doctorate.mixins import DoctorateAdmissionLastConfirmationMixin
from admission.views.mixins.business_exceptions_form_view_mixin import BusinessExceptionFormViewMixin
from infrastructure.messages_bus import message_bus_instance

__all__ = ["DoctorateAdmissionConfirmationFormView"]


class DoctorateAdmissionConfirmationFormView(
    DoctorateAdmissionLastConfirmationMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    template_name = 'admission/doctorate/forms/confirmation.html'
    form_class = ConfirmationForm
    permission_required = 'admission.change_doctorateadmission_confirmation'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['doctorate_status'] = self.doctorate.statut
        return kwargs

    def get_initial(self):
        return {
            'date_limite': self.last_confirmation_paper.date_limite,
            'date': self.last_confirmation_paper.date,
            'rapport_recherche': self.last_confirmation_paper.rapport_recherche,
            'proces_verbal_ca': self.last_confirmation_paper.proces_verbal_ca,
            'avis_renouvellement_mandat_recherche': self.last_confirmation_paper.avis_renouvellement_mandat_recherche,
        }

    def call_command(self, form):
        # Save the confirmation paper
        message_bus_instance.invoke(
            ModifierEpreuveConfirmationParCDDCommand(
                uuid=self.last_confirmation_paper.uuid,
                **form.cleaned_data,
            )
        )

    def get_success_url(self):
        return reverse('admission:doctorate:confirmation', args=[self.admission_uuid])
