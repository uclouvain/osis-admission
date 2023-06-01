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
from typing import Optional

import attr

from ddd.logic.learning_unit.domain.model.responsible_entity import UCLEntityIdentity, EntityCode
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class VerificateurIdentity(interface.EntityIdentity):
    code: attr.ib(type=EntityCode)


@attr.dataclass(slots=True, hash=False, eq=False)
class Verificateur(interface.RootEntity):
    entity_id: 'VerificateurIdentity'
    entite_ucl_id: 'UCLEntityIdentity'
    matricule: Optional[str]
