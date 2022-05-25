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
from django.views.generic import TemplateView

from admission.ddd.projet_doctoral.doctorat.commands import RecupererDoctoratQuery
from admission.ddd.projet_doctoral.doctorat.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.commands import (
    RecupererDerniereEpreuveConfirmationQuery,
)
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonTrouveeException,
)
from admission.utils import get_cached_admission_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import PermissionRequiredMixin


class DoctorateAdmissionExtensionRequestDetailView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'admission/doctorate/details/extension_request.html'
    permission_required = 'admission.view_doctorateadmission_confirmation'

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            results = message_bus_instance.invoke_multiple(
                [
                    RecupererDoctoratQuery(doctorat_uuid=kwargs.get('pk')),
                    RecupererDerniereEpreuveConfirmationQuery(doctorat_uuid=kwargs.get('pk')),
                ]
            )
        except (DoctoratNonTrouveException, EpreuveConfirmationNonTrouveeException) as e:
            raise Http404(e.message)

        context['doctorate'] = results[0]
        context['confirmation_paper'] = results[1]

        return context
