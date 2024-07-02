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

from django.http import Http404
from rest_framework.generics import RetrieveAPIView

from admission.api import serializers
from admission.api.schema import BetterChoicesSchema
from ddd.logic.formation_catalogue.formation_continue.commands import RecupererInformationsSpecifiquesQuery
from ddd.logic.formation_catalogue.formation_continue.domain.validator.exceptions import (
    InformationsSpecifiquesNonTrouveesException,
)
from infrastructure.messages_bus import message_bus_instance


class RetrieveContinuingEducationSpecificInformationView(RetrieveAPIView):
    name = 'retrieve-continuing-education-specific-information'
    schema = BetterChoicesSchema()
    filter_backends = []
    serializer_class = serializers.InformationsSpecifiquesFormationContinueDTOSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()

        context['acronym'] = self.kwargs.get('sigle')
        context['academic_year'] = self.kwargs.get('annee')

        return context

    def get_object(self):
        try:
            return message_bus_instance.invoke(
                RecupererInformationsSpecifiquesQuery(
                    sigle_formation=self.kwargs['sigle'],
                    annee=self.kwargs['annee'],
                )
            )
        except InformationsSpecifiquesNonTrouveesException:
            raise Http404
