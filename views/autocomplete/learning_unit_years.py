# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict, List

from django.conf import settings
from django.utils.translation import get_language, gettext_lazy

from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.enums.proposal_type import ProposalType
from ddd.logic.learning_unit.commands import (
    LearningUnitAndPartimSearchCommand,
    SearchDetailClassesEffectivesCommand,
)
from infrastructure.messages_bus import message_bus_instance
from learning_unit.views.autocomplete import (
    LearningUnitYearAutoComplete as BaseLearningUnitYearAutoComplete,
)

__all__ = [
    'LearningUnitYearAndClassesAutocomplete',
    'LearningUnitYearAutocomplete',
]

__namespace__ = False


class LearningUnitYearAndClassesAutocomplete(BaseLearningUnitYearAutoComplete):
    urlpatterns = 'learning-unit-years-and-classes'

    def get_list(self):
        sigle = self.q.upper()
        annee = self.forwarded.get('annee')
        types_a_exclure = [LearningContainerYearType.EXTERNAL.name]
        if not sigle or not annee:
            return []

        cmd = LearningUnitAndPartimSearchCommand(
            annee_academique=annee,
            terme_de_recherche=sigle,
            types_a_exclure=types_a_exclure,
        )
        result_unites_enseignement = message_bus_instance.invoke(cmd)

        cmd = SearchDetailClassesEffectivesCommand(
            annee=annee,
            terme_de_recherche=sigle,
            types_a_exclure=types_a_exclure,
        )
        result_classes = message_bus_instance.invoke(cmd)

        full_results = result_unites_enseignement + result_classes

        return sorted(full_results, key=lambda t: t.code if hasattr(t, "code") else t.code_complet_classe)


class LearningUnitYearAutocomplete(BaseLearningUnitYearAutoComplete):
    urlpatterns = 'learning-unit-years'
    title_attribute = {
        settings.LANGUAGE_CODE_FR: 'full_title',
        settings.LANGUAGE_CODE_EN: 'full_title_en',
    }
    prefix_icon = {ProposalType.SUPPRESSION.name: '<i class="far fa-file deleted-learning-unit-icon"></i>'}
    option_title = {ProposalType.SUPPRESSION.name: gettext_lazy('LU proposed for deletion')}

    def get_list(self):
        search = self.q
        year = self.forwarded.get('year')

        if not search or not year:
            return []

        return message_bus_instance.invoke(
            LearningUnitAndPartimSearchCommand(
                annee_academique=year,
                avec_mobilite=False,
                terme_de_recherche=search,
            )
        )

    def autocomplete_results(self, results):
        # Do nothing as we already filter in the `get_list` method
        return results

    def results(self, results) -> List[Dict]:
        results = [
            {
                'id': dto.code,
                'selected_text': (learning_title := self.get_learning_unit_title(dto)),
                'text': f'{self.prefix_icon.get(dto.proposal_type, "")}{learning_title}',
                'title': self.option_title.get(dto.proposal_type, ''),
                'disabled': dto.proposal_type == ProposalType.SUPPRESSION.name,
            }
            for dto in results
        ]
        return sorted(results, key=lambda elt: elt['selected_text'])

    @classmethod
    def get_learning_unit_title(cls, dto):
        title_attribute = cls.title_attribute[get_language()]
        return f"{dto.code} - {getattr(dto, title_attribute) or dto.full_title}"

    @classmethod
    def dtos_to_choices(cls, dtos):
        return [(dto.code, cls.get_learning_unit_title(dto)) for dto in dtos]
