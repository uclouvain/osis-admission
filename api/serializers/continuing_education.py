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
from rest_framework import serializers

from admission.utils import get_practical_information_url
from base.utils.serializers import DTOSerializer
from ddd.logic.formation_catalogue.commands import RecupererFormationQuery
from ddd.logic.formation_catalogue.domain.validators.exceptions import TrainingNotFoundException
from ddd.logic.formation_catalogue.dtos.training import TrainingDto
from ddd.logic.formation_catalogue.formation_continue.dtos.informations_specifiques import InformationsSpecifiquesDTO
from infrastructure.messages_bus import message_bus_instance


__all__ = [
    'InformationsSpecifiquesFormationContinueDTOSerializer',
]


class InformationsSpecifiquesFormationContinueDTOSerializer(DTOSerializer):
    etat = serializers.SerializerMethodField()
    lien_informations_pratiques_formation = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Define custom schemas as the default schema type of a SerializerMethodField is string
        self.fields['lien_informations_pratiques_formation'].field_schema = {
            'type': 'string',
        }

    def get_etat(self, obj):
        return obj.etat.name if obj.etat else ''

    def get_lien_informations_pratiques_formation(self, obj):
        if not self.context['acronym'] or not self.context['academic_year']:
            return ''

        try:
            training: TrainingDto = message_bus_instance.invoke(
                RecupererFormationQuery(
                    sigle_formation=self.context['acronym'],
                    annee_formation=self.context['academic_year'],
                )
            )
        except TrainingNotFoundException:
            return ''

        return get_practical_information_url(
            training_type=training.type,
            training_acronym=training.acronym,
            partial_training_acronym=training.code,
        )

    class Meta:
        source = InformationsSpecifiquesDTO
