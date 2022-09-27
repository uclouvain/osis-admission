# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from rest_framework import serializers

from admission.contrib.models.enums.actor_type import ActorType
from admission.ddd.admission.projet_doctoral.preparation.commands import (
    DesignerPromoteurReferenceCommand,
    IdentifierMembreCACommand,
    IdentifierPromoteurCommand,
    SupprimerMembreCACommand,
    SupprimerPromoteurCommand,
)
from admission.ddd.admission.projet_doctoral.preparation.dtos import GroupeDeSupervisionDTO
from base.models.person import Person
from base.utils.serializers import DTOSerializer


class SupervisionDTOSerializer(DTOSerializer):
    class Meta:
        source = GroupeDeSupervisionDTO


class SupervisionActorSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=ActorType.choices(),
    )
    member = serializers.CharField()


class IdentifierPromoteurCommandSerializer(DTOSerializer):
    class Meta:
        source = IdentifierPromoteurCommand


class IdentifierMembreCACommandSerializer(DTOSerializer):
    class Meta:
        source = IdentifierMembreCACommand


class DesignerPromoteurReferenceCommandSerializer(DTOSerializer):
    class Meta:
        source = DesignerPromoteurReferenceCommand


class SupprimerPromoteurCommandSerializer(DTOSerializer):
    class Meta:
        source = SupprimerPromoteurCommand


class SupprimerMembreCACommandSerializer(DTOSerializer):
    class Meta:
        source = SupprimerMembreCACommand


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = (
            'first_name',
            'last_name',
            'global_id',
        )


class TutorSerializer(PersonSerializer):
    first_name = serializers.ReadOnlyField(source='person.first_name')
    last_name = serializers.ReadOnlyField(source='person.last_name')
    global_id = serializers.ReadOnlyField(source='person.global_id')
