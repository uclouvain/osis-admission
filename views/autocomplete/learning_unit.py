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
from base.models.enums.learning_container_year_types import LearningContainerYearType
from ddd.logic.learning_unit.commands import LearningUnitAndPartimSearchCommand, SearchDetailClassesEffectivesCommand
from infrastructure.messages_bus import message_bus_instance
from learning_unit.views.autocomplete import LearningUnitYearAutoComplete


class LearningUnitYearAutocomplete(LearningUnitYearAutoComplete):
    def get_list(self):
        sigle = self.q.upper()
        annee = self.forwarded.get('annee')
        types_a_exclure = [LearningContainerYearType.EXTERNAL.name]
        if not sigle or not annee:
            return []

        cmd = LearningUnitAndPartimSearchCommand(annee_academique=annee, code=sigle, types_a_exclure=types_a_exclure)
        result_unites_enseignement = message_bus_instance.invoke(cmd)

        cmd = SearchDetailClassesEffectivesCommand(annee=annee, code=sigle, types_a_exclure=types_a_exclure)
        result_classes = message_bus_instance.invoke(cmd)

        full_results = result_unites_enseignement + result_classes

        return sorted(full_results, key=lambda t: t.code if hasattr(t, "code") else t.code_complet_classe)
