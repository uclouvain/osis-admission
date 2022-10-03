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
from admission.ddd.admission.domain.model.bourse import (
    BourseDoubleDiplomeIdentity,
    BourseInternationaleIdentity,
    BourseDoctoratIdentity,
    BourseErasmusMundusIdentity,
)
from admission.ddd.admission.domain.service.i_bourse import BourseIdentity
from admission.ddd.admission.enums.type_bourse import TypeBourse
from osis_common.ddd.interface import EntityIdentityBuilder, CommandRequest, DTO


class BourseIdentityBuilder(EntityIdentityBuilder):
    MAPPING_TYPE_IDENTITY = {
        TypeBourse.DOUBLE_TRIPLE_DIPLOMATION.name: BourseDoubleDiplomeIdentity,
        TypeBourse.BOURSE_INTERNATIONALE_DOCTORAT.name: BourseInternationaleIdentity,
        TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE.name: BourseDoctoratIdentity,
        TypeBourse.ERASMUS_MUNDUS.name: BourseErasmusMundusIdentity,
    }

    @classmethod
    def build_from_command(cls, cmd: 'CommandRequest') -> 'BourseIdentity':
        raise NotImplementedError

    @classmethod
    def build_from_repository_dto(cls, dto_object: 'DTO') -> 'BourseIdentity':
        raise NotImplementedError

    @classmethod
    def build_from_uuid(cls, type: str, uuid: str) -> 'BourseIdentity':
        return cls.MAPPING_TYPE_IDENTITY[type](uuid=uuid)
