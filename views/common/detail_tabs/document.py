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
from django.views.generic import TemplateView

from admission.ddd.admission.enums.document import DOCUMENTS_UCLOUVAIN
from admission.ddd.admission.formation_generale import commands as general_education_commands
from admission.templatetags.admission import CONTEXT_GENERAL
from admission.views.doctorate.mixins import LoadDossierViewMixin
from infrastructure.messages_bus import message_bus_instance


__all__ = [
    'DocumentView',
]


class DocumentView(LoadDossierViewMixin, TemplateView):
    template_name = 'admission/document/base.html'
    permission_required = 'admission.view_documents_management'
    urlpatterns = 'document'

    retrieve_documents_command = {
        CONTEXT_GENERAL: general_education_commands.RecupererDocumentsDemandeQuery,
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['documents'] = (
            message_bus_instance.invoke(
                self.retrieve_documents_command[self.current_context](
                    uuid_demande=self.admission_uuid,
                )
            )
            if self.current_context in self.retrieve_documents_command
            else []
        )

        context['DOCUMENTS_UCLOUVAIN'] = DOCUMENTS_UCLOUVAIN

        return context
