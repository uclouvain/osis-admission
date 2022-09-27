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

from django.http import Http404
from django.views.generic import TemplateView

from admission.ddd.doctorat.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.doctorat.epreuve_confirmation.commands import RecupererEpreuvesConfirmationQuery
from admission.ddd.doctorat.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from admission.mail_templates import ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT
from admission.views.doctorate.mixins import LoadDossierViewMixin
from infrastructure.messages_bus import message_bus_instance


class DoctorateAdmissionConfirmationDetailView(LoadDossierViewMixin, TemplateView):
    template_name = 'admission/doctorate/details/confirmation.html'
    permission_required = 'admission.view_doctorateadmission_confirmation'
    mandatory_fields_for_evaluation = [
        'date',
        'proces_verbal_ca',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            all_confirmation_papers: List[EpreuveConfirmationDTO] = message_bus_instance.invoke(
                RecupererEpreuvesConfirmationQuery(doctorat_uuid=self.admission_uuid),
            )
        except DoctoratNonTrouveException as e:
            raise Http404(e.message)

        if all_confirmation_papers:
            current_confirmation_paper = all_confirmation_papers.pop(0)
            context['can_be_evaluated'] = all(
                getattr(current_confirmation_paper, field) for field in self.mandatory_fields_for_evaluation
            )
            context['current_confirmation_paper'] = current_confirmation_paper

        context['previous_confirmation_papers'] = all_confirmation_papers
        context['INFO_TEMPLATE_IDENTIFIER'] = ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT

        return context
