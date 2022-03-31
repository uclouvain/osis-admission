##############################################################################
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
##############################################################################
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from admission.auth.mixins import CddRequiredMixin
from admission.ddd.projet_doctoral.preparation.commands import GetPropositionCommand
from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixStatutProposition
from admission.ddd.projet_doctoral.validation.commands import RecupererDemandeQuery
from infrastructure.messages_bus import message_bus_instance


class LoadDossierViewMixin(LoginRequiredMixin, CddRequiredMixin, TemplateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get proposition information
        proposition = message_bus_instance.invoke((
            GetPropositionCommand(uuid_proposition=kwargs.get('pk'))
        ))

        context['admission'] = proposition

        # Add the dossier information if there are some
        if proposition.statut == ChoixStatutProposition.SUBMITTED.name:
            dossier = message_bus_instance.invoke(
                RecupererDemandeQuery(uuid=kwargs.get('pk')),
            )
            context['dossier'] = dossier

        return context
