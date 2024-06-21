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

from base.models.enums.establishment_type import EstablishmentTypeEnum
from reference.models.diploma_title import DiplomaTitle, get_diploma_label_with_study_type
from reference.models.enums.study_type import StudyType

__all__ = [
    'DiplomaTitleAutocomplete',
]


def get_diploma_label(diploma_title: DiplomaTitle) -> str:
    return diploma_title.title


# TODO to move into reference
class DiplomaTitleAutocomplete(autocomplete.Select2QuerySetView):
    urlpatterns = 'diploma-title'

    def get_queryset(self):
        queryset = DiplomaTitle.objects.filter(active=True)

        establishment_type = self.forwarded.get('establishment_type')
        if establishment_type:
            establishment_study_type = {
                EstablishmentTypeEnum.UNIVERSITY.name: StudyType.UNIVERSITY.name,
                EstablishmentTypeEnum.NON_UNIVERSITY_HIGHER.name: StudyType.NON_UNIVERSITY.name,
            }.get(establishment_type)

            if establishment_study_type:
                queryset = queryset.filter(study_type=establishment_study_type)

        study_type = self.forwarded.get('study_type')
        if study_type:
            queryset = queryset.filter(study_type=study_type)

        if self.q:
            queryset = queryset.filter(title__unaccent__icontains=self.q)

        return queryset.order_by('title')

    def get_results(self, context):
        """Return data for the 'results' key of the response."""
        get_label_function = (
            get_diploma_label_with_study_type if self.forwarded.get('display_study_type') else get_diploma_label
        )

        return [
            {
                'id': self.get_result_value(result),
                'text': get_label_function(result),
                'selected_text': get_label_function(result),
                'cycle': result.cycle,
            }
            for result in context['object_list']
        ]
