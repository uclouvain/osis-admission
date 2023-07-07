# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Dict

from dal_select2.views import Select2ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse

from admission.ddd.admission.formation_generale.commands import RechercherFormationsGereesQuery
from admission.ddd.admission.dtos.formation import BaseFormationDTO
from admission.ddd.admission.formation_generale.commands import RechercherFormationGeneraleQuery
from infrastructure.messages_bus import message_bus_instance

__namespace__ = False


__all__ = [
    'GeneralEducationTrainingsAutocomplete',
    'ManagedGeneralEducationTrainingsAutocomplete',
]


class GeneralEducationTrainingsAutocomplete(LoginRequiredMixin, Select2ListView):
    urlpatterns = 'general-education-trainings'

    def get(self, request, *args, **kwargs):
        education_list = message_bus_instance.invoke(
            RechercherFormationGeneraleQuery(
                terme_de_recherche=self.q,
                annee=self.forwarded.get('annee_academique'),
            )
        )

        results = [
            {
                'id': formation.sigle,
                'text': f'{formation.sigle} - {formation.intitule}',
            }
            for formation in education_list
        ]
        return JsonResponse(
            {
                'pagination': {'more': False},
                'results': results,
            },
            content_type='application/json',
        )


class ManagedGeneralEducationTrainingsAutocomplete(LoginRequiredMixin, Select2ListView):
    urlpatterns = 'managed-general-education-trainings'

    def get_list(self) -> List[BaseFormationDTO]:
        return message_bus_instance.invoke(
            RechercherFormationsGereesQuery(
                terme_recherche=self.q,
                annee=self.forwarded.get('annee_academique'),
                matricule_gestionnaire=self.request.user.person.global_id,
            )
        )

    def autocomplete_results(self, results):
        # Do nothing as we already filter in get_list
        return results

    def results(self, results: List[BaseFormationDTO]) -> List[Dict]:
        return [
            {
                'id': str(result.uuid),
                'text': f'{result.sigle} - {result.intitule} ({result.lieu_enseignement})',
            }
            for result in results
        ]
