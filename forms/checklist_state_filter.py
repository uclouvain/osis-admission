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
from typing import List

from django import forms

from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    ConfigurationOngletChecklist,
)

__all__ = [
    'ChecklistStateFilterField',
    'CheckListStateFilterWidget',
]


class ChecklistStateFilterField(forms.MultiValueField):
    """
    Field used to filter the admissions on checklist state by displaying a checkbox for each checklist state.
    """

    def __init__(self, configurations: List[ConfigurationOngletChecklist], *args, **kwargs):
        fields = []
        widgets = []

        for config in configurations:
            field = forms.MultipleChoiceField(
                label=config.identifiant.value,
                choices=[(status.identifiant, status.libelle) for status in config.statuts],
                required=False,
                widget=forms.CheckboxSelectMultiple(),
            )
            fields.append(field)
            widgets.append(field.widget)

        self.configurations = configurations

        super().__init__(
            fields=fields,
            require_all_fields=False,
            widget=CheckListStateFilterWidget(widgets=widgets, configurations=configurations, fields=fields),
            *args,
            **kwargs,
        )

    def compress(self, data_list):
        try:
            return {config.identifiant.name: data_list[index] for index, config in enumerate(self.configurations)}
        except IndexError:
            return {}


class CheckListStateFilterWidget(forms.MultiWidget):
    """
    Widget used to filter the admissions on checklist state by displaying a checkbox for each checklist state.
    """

    template_name = 'admission/widgets/multiwidget.html'

    def __init__(self, configurations: List[ConfigurationOngletChecklist], fields: List[forms.Field], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configurations = configurations
        self.fields = fields

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context['configurations'] = self.configurations
        context['fields'] = list(zip(context['widget']['subwidgets'], self.fields))
        return context

    def decompress(self, value):
        if not value:
            value = {}
        return [value.get(config.identifiant.name) for config in self.configurations]
