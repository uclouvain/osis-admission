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

from admission.ddd.parcours_doctoral.jury.commands import ModifierJuryCommand
from admission.forms.doctorate.jury.preparation import JuryPreparationForm
from admission.views.doctorate.mixins import LoadDossierViewMixin
from admission.views.mixins.business_exceptions_form_view_mixin import BusinessExceptionFormViewMixin
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    "DoctorateAdmissionJuryPreparationFormView",
]

__namespace__ = False


class DoctorateAdmissionJuryPreparationFormView(
    LoadDossierViewMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    urlpatterns = 'jury-preparation'
    template_name = 'admission/doctorate/forms/jury/preparation.html'
    permission_required = 'admission.change_admission_jury'
    form_class = JuryPreparationForm

    def get_initial(self):
        return {
            'titre_propose': self.jury.titre_propose,
            'formule_defense': self.jury.formule_defense,
            'date_indicative': self.jury.date_indicative,
            'langue_redaction': self.jury.langue_redaction,
            'langue_soutenance': self.jury.langue_soutenance,
            'commentaire': self.jury.commentaire,
        }

    def call_command(self, form):
        message_bus_instance.invoke(
            ModifierJuryCommand(
                uuid_doctorat=self.admission_uuid,
                **form.cleaned_data,
            )
        )

    def get_success_url(self):
        return reverse('admission:doctorate:jury-preparation', args=[self.admission_uuid])
