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
import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True, eq=False)
class PropositionFusionPersonneDTO(interface.DTO):
    status: str
    matricule: str
    original_person_uuid: str
    last_name: str
    first_name: str
    other_name: str
    sex: str
    gender: str
    birth_date: str
    birth_country: str
    birth_place: str
    civil_state: str
    country_of_citizenship: str
    national_number: str
    passport_number: str
    id_card_number: str
    id_card_expiry_date: str
    professional_curex_uuids: str
    educational_curex_uuids: str
