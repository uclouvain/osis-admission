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
from django.views.generic import RedirectView

from admission.ddd.projet_doctoral.preparation.commands import GetGroupeDeSupervisionCommand
from admission.exports.admission_confirmation_canvas import admission_pdf_confirmation_canvas
from admission.views.doctorate.forms.confirmation import DoctorateAdmissionLastConfirmationMixin
from infrastructure.messages_bus import message_bus_instance


class DoctorateAdmissionConfirmationCanvasExportView(DoctorateAdmissionLastConfirmationMixin, RedirectView):
    permission_required = 'admission.view_doctorateadmission_confirmation'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        context_data['supervision_group'] = message_bus_instance.invoke(
            GetGroupeDeSupervisionCommand(uuid_proposition=self.kwargs.get('pk')),
        )
        return context_data

    def get(self, request, *args, **kwargs):
        from osis_document.utils import get_file_url
        from osis_document.api.utils import get_remote_token

        file_uuid = admission_pdf_confirmation_canvas(
            admission=self.admission,
            language=self.admission.candidate.language,
            context=self.get_context_data(),
        )
        reading_token = get_remote_token(file_uuid)

        self.url = get_file_url(reading_token)

        return super().get(request, *args, **kwargs)
