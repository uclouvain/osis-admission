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
import uuid
from typing import Optional, List

from admission.ddd.admission.dtos.proposition_fusion_personne import PropositionFusionPersonneDTO
from admission.ddd.admission.dtos.statut_ticket_personne import StatutTicketPersonneDTO
from admission.ddd.admission.repository.i_digit import IDigitRepository
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


class DigitInMemoryRepository(InMemoryGenericRepository, IDigitRepository):
    statut_ticket = StatutTicketPersonneDTO(
        request_id=1,
        matricule='123456789',
        noma='0000000',
        nom='lastname',
        prenom='firstname',
        statut='CREATED',
        errors=[],
        type_fusion="MEGE",
        uuid="43f8dc86-5a77-4852-a0a0-1efc994cf843",
    )

    @classmethod
    def submit_person_ticket(cls, global_id: str, noma: str):
        pass

    @classmethod
    def get_last_person_ticket_status(cls, global_id: str) -> Optional[StatutTicketPersonneDTO]:
        return cls.statut_ticket

    @classmethod
    def retrieve_person_ticket_status_from_digit(cls, ticket_uuid: str) -> Optional[str]:
        return cls.statut_ticket.statut

    @classmethod
    def retrieve_list_pending_person_tickets(cls) -> List[StatutTicketPersonneDTO]:
        return [cls.statut_ticket]

    @classmethod
    def retrieve_list_error_merge_proposals(cls) -> List[PropositionFusionPersonneDTO]:
        raise []

    @classmethod
    def get_registration_id_sent_to_digit(cls, global_id: str) -> Optional[str]:
        return None

    @classmethod
    def has_digit_creation_ticket(cls, global_id: str) -> bool:
        return False
