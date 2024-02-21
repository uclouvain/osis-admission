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
import json
from typing import Optional, List

import requests
from django.conf import settings

from admission.ddd.admission.dtos.statut_ticket_personne import StatutTicketPersonneDTO
from admission.ddd.admission.repository.i_digit import IDigitRepository
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.models.person_creation_ticket import PersonTicketCreation, PersonTicketCreationStatus
from base.models.person_merge_proposal import PersonMergeProposal


class DigitRepository(IDigitRepository):
    @classmethod
    def submit_person_ticket(cls, global_id: str, noma: str):
        person = Person.objects.get(global_id=global_id)

        # get proposal merge person if any is linked
        proposition = PersonMergeProposal.objects.filter(original_person=person, proposal_merge_person__isnull=False)
        if proposition.exists():
            person = proposition.get().proposal_merge_person

        ticket_response = _request_person_ticket_creation(person, noma)

        if ticket_response:
            PersonTicketCreation.objects.get_or_create(
                request_id=ticket_response['requestId'], status=ticket_response['status']
            )

    @classmethod
    def get_person_ticket_status(cls, global_id: str) -> Optional[StatutTicketPersonneDTO]:
        try:
            ticket = PersonTicketCreation.objects.select_related('person').get(person__global_id=global_id)
            return StatutTicketPersonneDTO(
                request_id=ticket.request_id,
                matricule=ticket.person.global_id,
                nom=ticket.person.last_name,
                prenom=ticket.person.first_name,
                statut=ticket.status,
                errors=[error['msg'] for error in ticket.errors],
            )
        except PersonTicketCreation.DoesNotExist:
            return None

    @classmethod
    def retrieve_person_ticket_status_from_digit(cls, global_id: str) -> Optional[str]:
        if PersonTicketCreation.objects.filter(person__global_id=global_id).exists():
            stored_ticket = PersonTicketCreation.objects.get(person__global_id=global_id)
            remote_ticket = _retrieve_person_ticket_status(stored_ticket.request_id)
            if remote_ticket:
                stored_ticket.status = remote_ticket['status']
                stored_ticket.errors = remote_ticket['errors'] if 'errors' in remote_ticket.keys() else []
                stored_ticket.save()
            return remote_ticket['status']
        else:
            return None

    @classmethod
    def retrieve_list_pending_person_tickets(cls) -> List[StatutTicketPersonneDTO]:
        tickets = PersonTicketCreation.objects.filter(
            status=PersonTicketCreationStatus.CREATED.value
        ).select_related('person').values(
            'request_id', 'person__last_name', 'person__first_name', 'person__global_id', 'status', 'errors'
        )
        return [
            StatutTicketPersonneDTO(
                request_id=ticket['request_id'],
                matricule=ticket['person__global_id'],
                nom=ticket['person__last_name'],
                prenom=ticket['person__first_name'],
                statut=ticket['status'],
                errors=[error['msg'] for error in ticket['errors']],
            ) for ticket in tickets
        ]


def _retrieve_person_ticket_status(request_id: int):
    if settings.MOCK_DIGIT_SERVICE_CALL:
        return {
            "requestId": "1",
            "status": "DONE_WITH_ERRORS",
            "errors": [
                {
                    "msg": "Le format du numéro national: (85073015002)  est incorrect.",
                    "errorCode": {
                        "errorCode": "INISS0003",
                        "description": "Le format du numéro national est incorrect",
                        "quarantine": True,
                        "exclude": False
                    }
                },
            ],
        }
    return requests.get(
        headers={
            'Content-Type': 'application/json',
            'Authorization': settings.ESB_AUTHORIZATION,
        },
        url=f"{settings.ESB_API_URL}/{settings.DIGIT_ACCOUNT_REQUEST_STATUS_URL}/{request_id}"
    ).json()


def _request_person_ticket_creation(person: Person, noma: str):
    if settings.MOCK_DIGIT_SERVICE_CALL:
        return {"requestId": "1", "status": "CREATED"}
    else:
        response = requests.post(
            headers={
                'Content-Type': 'application/json',
                'Authorization': settings.ESB_AUTHORIZATION,
            },
            data=json.dumps(_get_ticket_data(person, noma)),
            url=f"{settings.ESB_API_URL}/{settings.DIGIT_ACCOUNT_CREATION_URL}"
        )
        return response.json()


def _get_ticket_data(person: Person, noma: str):
    return {
        "provider": {
            "source": "ETU",
            "sourceId": noma,
            "actif": True,
        },
        "person": {
            "matricule": person.global_id,
            "lastName": person.last_name,
            "firstName": person.first_name,
            "birthDate": person.birth_date.strftime('%Y-%m-%d'),
            "gender": person.gender,
            "nationalRegister": person.national_number,
            "nationality": person.country_of_citizenship.iso_code,
        },
        "addresses": [
            {
                "addressType": "RES",
                "country": address.country.iso_code,
                "postalCode": address.postal_code,
                "locality": address.city,
                "street": address.street,
                "number": address.street_number,
                "box": address.postal_box,
                "additionalAddressDetails": [],
            }
            for address in person.personaddress_set.filter(label=PersonAddressType.RESIDENTIAL.name)
        ],
        "physicalPerson": True,
    }
