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
import attr
from django.shortcuts import resolve_url
from django.views.generic import FormView

from admission.ddd.admission.doctorat.preparation.commands import DefinirCotutelleCommand
from admission.forms.admission.doctorate.cotutelle import DoctorateAdmissionCotutelleForm
from admission.infrastructure.admission.doctorat.preparation.repository.groupe_de_supervision import (
    GroupeDeSupervisionRepository,
)
from admission.views.common.mixins import LoadDossierViewMixin

__all__ = [
    "DoctorateAdmissionCotutelleFormView",
]

from admission.views.mixins.business_exceptions_form_view_mixin import BusinessExceptionFormViewMixin
from infrastructure.messages_bus import message_bus_instance


class DoctorateAdmissionCotutelleFormView(
    LoadDossierViewMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    template_name = 'admission/doctorate/forms/cotutelle.html'
    permission_required = 'admission.change_admission_cotutelle'
    form_class = DoctorateAdmissionCotutelleForm

    def get_success_url(self):
        return resolve_url('admission:doctorate:cotutelle', uuid=self.admission_uuid)

    def get_initial(self):
        cotutelle = GroupeDeSupervisionRepository.get_cotutelle_dto(self.admission_uuid)
        initial = attr.asdict(cotutelle)
        if initial['cotutelle'] is not None:
            initial['cotutelle'] = 'YES' if initial['cotutelle'] else 'NO'
            if initial['institution_fwb'] is not None:
                initial['institution_fwb'] = 'true' if initial['institution_fwb'] else 'false'
        return initial

    def prepare_data(self, data: dict):
        if data['cotutelle'] == 'NO':
            data.update(
                motivation="",
                institution_fwb=None,
                institution="",
                demande_ouverture=[],
                convention=[],
                autres_documents=[],
            )
        del data['cotutelle']
        del data['autre_institution']
        return data

    def call_command(self, form):
        # Save the confirmation paper
        message_bus_instance.invoke(
            DefinirCotutelleCommand(
                uuid_proposition=self.admission_uuid,
                matricule_auteur=self.request.user.person.global_id,
                **self.prepare_data(form.cleaned_data),
            )
        )
