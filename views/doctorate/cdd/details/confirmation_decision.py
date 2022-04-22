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
from django.contrib.messages import error
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.views import View

from admission.auth.mixins import CddRequiredMixin
from admission.ddd.projet_doctoral.doctorat.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.commands import (
    ConfirmerReussiteCommand,
    RecupererDerniereEpreuveConfirmationQuery,
)
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonTrouveeException,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance


class CddDoctorateAdmissionConfirmationSuccessDecisionView(LoginRequiredMixin, CddRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            last_confirmation_paper: EpreuveConfirmationDTO = message_bus_instance.invoke(
                RecupererDerniereEpreuveConfirmationQuery(doctorat_uuid=self.kwargs.get('pk'))
            )
            message_bus_instance.invoke(ConfirmerReussiteCommand(uuid=last_confirmation_paper.uuid))
            return HttpResponseRedirect(reverse('admission:doctorate:cdd:confirmation', kwargs=kwargs))
        except (DoctoratNonTrouveException, EpreuveConfirmationNonTrouveeException) as e:
            raise Http404(e.message)
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                error(request, exception.message)
            return HttpResponseRedirect(reverse('admission:doctorate:cdd:confirmation', kwargs=kwargs))
