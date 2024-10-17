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
from dal import autocomplete
from django.utils.translation import get_language

from admission.models.working_list import WorkingList, ContinuingWorkingList, DoctorateWorkingList
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_POUR_LISTING,
)
from admission.ddd.admission.formation_continue.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST as ORGANISATION_ONGLETS_CHECKLIST_CONTINUE,
)
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST as ORGANISATION_ONGLETS_CHECKLIST_GENERALE,
)

__namespace__ = False


__all__ = [
    'WorkingListAutocomplete',
    'ContinuingWorkingListAutocomplete',
    'DoctorateWorkingListAutocomplete',
]


class WorkingListAutocomplete(autocomplete.Select2QuerySetView):
    model = WorkingList
    urlpatterns = 'working-lists'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_language = get_language()
        self.model_field_name = f'name__{self.current_language}'

    def get_result_label(self, result: WorkingList):
        return result.name.get(self.current_language)

    def get_results(self, context):
        return [
            {
                'id': result.id,
                'text': result.name.get(self.current_language),
                'checklist_filters_mode': result.checklist_filters_mode,
                'checklist_filters': [
                    result.checklist_filters.get(checklist_tab.identifiant.name, [])
                    for checklist_tab in ORGANISATION_ONGLETS_CHECKLIST_GENERALE
                ],
                'admission_statuses': result.admission_statuses,
                'admission_type': result.admission_type,
                'quarantine': result.quarantine,
            }
            for result in context['object_list']
        ]


class ContinuingWorkingListAutocomplete(WorkingListAutocomplete):
    model = ContinuingWorkingList
    urlpatterns = 'continuing-working-lists'

    def get_results(self, context):
        return [
            {
                'id': result.id,
                'text': result.name.get(self.current_language),
                'checklist_filters_mode': result.checklist_filters_mode,
                'checklist_filters': [
                    result.checklist_filters.get(checklist_tab.identifiant.name, [])
                    for checklist_tab in ORGANISATION_ONGLETS_CHECKLIST_CONTINUE
                ],
                'admission_statuses': result.admission_statuses,
            }
            for result in context['object_list']
        ]


class DoctorateWorkingListAutocomplete(WorkingListAutocomplete):
    model = DoctorateWorkingList
    urlpatterns = 'doctorate-working-lists'

    def get_results(self, context):
        return [
            {
                'id': result.id,
                'text': result.name.get(self.current_language),
                'checklist_filters_mode': result.checklist_filters_mode,
                'checklist_filters': [
                    result.checklist_filters.get(checklist_tab.identifiant.name, [])
                    for checklist_tab in ORGANISATION_ONGLETS_CHECKLIST_POUR_LISTING
                ],
                'admission_statuses': result.admission_statuses,
                'admission_type': result.admission_type,
            }
            for result in context['object_list']
        ]
