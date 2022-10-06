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
from typing import List, Dict

from admission.contrib.models import Scholarship
from admission.ddd.admission.domain.builder.bourse_identity import BourseIdentityBuilder

from admission.ddd.admission.domain.service.i_bourse import IBourseTranslator, BourseIdentity
from admission.ddd.admission.domain.validator.exceptions import BourseNonTrouveeException
from admission.ddd.admission.dtos.bourse import BourseDTO


class BourseTranslator(IBourseTranslator):
    @classmethod
    def get(cls, uuid: str) -> BourseIdentity:
        if not cls.verifier_existence(uuid=uuid):
            raise BourseNonTrouveeException
        return BourseIdentityBuilder.build_from_uuid(uuid=uuid)

    @classmethod
    def get_dto(cls, uuid: str) -> BourseDTO:
        try:
            scholarship = Scholarship.objects.get(pk=uuid)
            return cls.build_dto(scholarship)
        except Scholarship.DoesNotExist:
            raise BourseNonTrouveeException

    @classmethod
    def search(cls, uuids: List[str]) -> Dict[str, BourseIdentity]:
        if uuids:
            scholarships = {
                str(scholarship.uuid): BourseIdentityBuilder.build_from_uuid(uuid=scholarship.uuid)
                for scholarship in Scholarship.objects.filter(uuid__in=uuids)
            }
            if len(scholarships) != len(uuids):
                raise BourseNonTrouveeException
            return scholarships
        return {}

    @classmethod
    def search_dto(cls, uuids: List[str]) -> Dict[str, BourseDTO]:
        if uuids:
            scholarships = {
                str(scholarship.uuid): cls.build_dto(scholarship)
                for scholarship in Scholarship.objects.filter(uuid__in=uuids)
            }
            if len(scholarships) != len(uuids):
                raise BourseNonTrouveeException
            return scholarships
        return {}

    @classmethod
    def build_dto(cls, scholarship: Scholarship) -> BourseDTO:
        return BourseDTO(
            nom_court=scholarship.short_name,
            nom_long=scholarship.long_name,
            type=scholarship.type,
            uuid=str(scholarship.uuid),
        )

    @classmethod
    def verifier_existence(cls, uuid: str) -> bool:
        return Scholarship.objects.filter(pk=uuid).exists()
