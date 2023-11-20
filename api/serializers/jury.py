# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.utils.serializers import DTOSerializer
from admission.ddd.parcours_doctoral.jury.commands import (
    ModifierJuryCommand,
    AjouterMembreCommand,
    ModifierMembreCommand,
    RetirerMembreCommand,
    ModifierRoleMembreCommand,
)
from admission.ddd.parcours_doctoral.jury.dtos.jury import JuryDTO, MembreJuryDTO

__all__ = [
    'JuryDTOSerializer',
    'JuryIdentityDTOSerializer',
    'MembreJuryDTOSerializer',
    'MembreJuryIdentityDTOSerializer',
    'ModifierJuryCommandSerializer',
    'AjouterMembreCommandSerializer',
    'ModifierMembreCommandSerializer',
    'ModifierRoleMembreCommandSerializer',
]


class JuryDTOSerializer(DTOSerializer):
    class Meta:
        source = JuryDTO


class JuryIdentityDTOSerializer(serializers.Serializer):
    uuid = serializers.ReadOnlyField()


class MembreJuryDTOSerializer(DTOSerializer):
    class Meta:
        source = MembreJuryDTO


class MembreJuryIdentityDTOSerializer(serializers.Serializer):
    uuid = serializers.ReadOnlyField()


class ModifierJuryCommandSerializer(DTOSerializer):
    uuid_doctorat = None

    class Meta:
        source = ModifierJuryCommand


class AjouterMembreCommandSerializer(DTOSerializer):
    uuid_jury = None

    class Meta:
        source = AjouterMembreCommand


class ModifierMembreCommandSerializer(DTOSerializer):
    uuid_jury = None
    uuid_membre = None

    class Meta:
        source = ModifierMembreCommand


class ModifierRoleMembreCommandSerializer(DTOSerializer):
    uuid_jury = None
    uuid_membre = None

    class Meta:
        source = ModifierRoleMembreCommand
