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
from abc import ABCMeta
from typing import List, Optional

from admission.ddd.admission.domain.model.proposition_fusion_personne import PropositionFusionPersonneIdentity
from admission.ddd.admission.dtos.proposition_fusion_personne import PropositionFusionPersonneDTO
from osis_common.ddd import interface


class IDigitRepository:
    @classmethod
    def submit_person_ticket(cls, global_id: str, noma: str) -> any:
        raise NotImplementedError

    @classmethod
    def get_person_ticket_status(cls, global_id: str) -> Optional[str]:
        raise NotImplementedError

    @classmethod
    def retrieve_person_ticket_status_from_digit(cls, global_id: str) -> Optional[str]:
        raise NotImplementedError
