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

from admission.ddd.admission.dtos.formation import BaseFormationDTO
from admission.ddd.admission.shared_kernel.role.commands import RechercherFormationsGereesQuery
from infrastructure.messages_bus import message_bus_instance

__namespace__ = False


__all__ = [
    'ManagedEducationTrainingsAutocomplete',
]


class ManagedEducationTrainingsAutocomplete(LoginRequiredMixin, Select2ListView):
    urlpatterns = 'managed-education-trainings'

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
