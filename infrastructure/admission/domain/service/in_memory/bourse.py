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
from uuid import uuid4
from dataclasses import dataclass
from typing import Optional, List, Dict

from admission.ddd.admission.domain.builder.bourse_identity import BourseIdentityBuilder
from admission.ddd.admission.domain.model.bourse import BourseDoubleDiplomeIdentity
from admission.ddd.admission.domain.service.i_bourse import IBourseTranslator, BourseIdentity
from admission.ddd.admission.domain.validator.exceptions import BourseNonTrouveeException
from admission.ddd.admission.dtos.bourse import BourseDTO
from admission.ddd.admission.enums.type_bourse import TypeBourse


@dataclass
class Bourse:
    entity_id: BourseIdentity
    type: TypeBourse
    nom_court: str
    nom_long: Optional[str] = ''


class BourseInMemoryTranslator(IBourseTranslator):
    bourse_dd_1 = Bourse(
        entity_id=BourseDoubleDiplomeIdentity(uuid=str(uuid4())),
        type=TypeBourse.DOUBLE_TRIPLE_DIPLOMATION,
        nom_court='AGRO DD UCLOUVAIN/GEM',
        nom_long='AGRO DD UCLOUVAIN/GEM --',
    )
    bourse_dd_2 = Bourse(
        entity_id=BourseDoubleDiplomeIdentity(uuid=str(uuid4())),
        type=TypeBourse.DOUBLE_TRIPLE_DIPLOMATION,
        nom_court='CRIM DD UCL/LILLE',
        nom_long='CRIM DD UCL/LILLE --',
    )
    bourse_ifg_1 = Bourse(
        entity_id=BourseDoubleDiplomeIdentity(uuid=str(uuid4())),
        type=TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE,
        nom_court='AFEPA',
        nom_long='AFEPA --',
    )
    bourse_ifg_2 = Bourse(
        entity_id=BourseDoubleDiplomeIdentity(uuid=str(uuid4())),
        type=TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE,
        nom_court='WBI',
        nom_long='WBI --',
    )
    bourse_em_1 = Bourse(
        entity_id=BourseDoubleDiplomeIdentity(uuid=str(uuid4())),
        type=TypeBourse.ERASMUS_MUNDUS,
        nom_court='EMDI',
        nom_long='EMDI --',
    )

    ENTITIES = [
        bourse_dd_1,
        bourse_dd_2,
        bourse_ifg_1,
        bourse_ifg_2,
        bourse_em_1,
    ]

    @classmethod
    def get(cls, uuid: str) -> BourseIdentity:
        scholarship = next((entity for entity in cls.ENTITIES if entity.entity_id.uuid == uuid), None)
        if scholarship:
            return scholarship.entity_id
        raise BourseNonTrouveeException

    @classmethod
    def get_dto(cls, uuid: str) -> BourseDTO:
        scholarship = next((entity for entity in cls.ENTITIES if entity.entity_id.uuid == uuid), None)
        if scholarship:
            return BourseDTO(
                type=scholarship.type.name,
                nom_court=scholarship.nom_court,
                nom_long=scholarship.nom_long,
            )
        raise BourseNonTrouveeException

    @classmethod
    def search(cls, uuids: List[str]) -> Dict[str, BourseIdentity]:
        if uuids:
            scholarships = {
                scholarship.entity_id.uuid: BourseIdentityBuilder.build_from_uuid(
                    type=scholarship.type.name,
                    uuid=scholarship.entity_id.uuid,
                )
                for scholarship in cls.ENTITIES
                if scholarship.entity_id.uuid in uuids
            }
            if len(scholarships) != len(uuids):
                raise BourseNonTrouveeException
            return scholarships
        return {}

    @classmethod
    def search_dto(cls, uuids: List[str]) -> Dict[str, BourseDTO]:
        if uuids:
            scholarships = {
                entity.entity_id.uuid: BourseDTO(
                    nom_court=entity.nom_court,
                    nom_long=entity.nom_long,
                    type=entity.type.name,
                )
                for entity in cls.ENTITIES
                if entity.entity_id.uuid in uuids
            }
            if len(scholarships) != len(uuids):
                raise BourseNonTrouveeException
            return scholarships

        return {}
