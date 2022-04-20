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
from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import TemplateView

from admission.auth.mixins import CddRequiredMixin
from admission.ddd.projet_doctoral.doctorat.commands import RecupererDoctoratQuery
from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.projet_doctoral.doctorat.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.commands import RecupererEpreuvesConfirmationQuery
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from infrastructure.messages_bus import message_bus_instance


class CddDoctorateAdmissionConfirmationDetailView(LoginRequiredMixin, CddRequiredMixin, TemplateView):
    template_name = 'admission/doctorate/cdd/details/confirmation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            results = message_bus_instance.invoke_multiple([
                RecupererDoctoratQuery(doctorat_uuid=kwargs.get('pk')),
                RecupererEpreuvesConfirmationQuery(doctorat_uuid=kwargs.get('pk')),
            ])
        except DoctoratNonTrouveException as e:
            raise Http404(e.message)

        context['doctorate'] = results[0]
        all_confirmation_papers: List[EpreuveConfirmationDTO] = results[1]

        if all_confirmation_papers:
            context['current_confirmation_paper'] = all_confirmation_papers.pop(0)

        context['previous_confirmation_papers'] = all_confirmation_papers

        return context
