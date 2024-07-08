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
import contextlib
import json
import logging
from datetime import datetime
from typing import Optional, List

import requests
import waffle
from django.conf import settings
from django.db.models import QuerySet, Q
from django.utils.datetime_safe import date

from admission.ddd.admission.dtos.proposition_fusion_personne import PropositionFusionPersonneDTO
from admission.ddd.admission.dtos.statut_ticket_personne import StatutTicketPersonneDTO
from admission.ddd.admission.dtos.validation_ticket_response import ValidationTicketResponseDTO
from admission.ddd.admission.repository.i_digit import IDigitRepository
from admission.infrastructure.admission.domain.service.digit import TEMPORARY_ACCOUNT_GLOBAL_ID_PREFIX
from admission.templatetags.admission import format_matricule
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.models.person_creation_ticket import PersonTicketCreation, PersonTicketCreationStatus
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus

logger = logging.getLogger(settings.DEFAULT_LOGGER)


class DigitRepository(IDigitRepository):
    @classmethod
    def submit_person_ticket(cls, global_id: str, noma: str, extra_ticket_data: dict = None):
        candidate = Person.objects.get(global_id=global_id)
        if extra_ticket_data is None:
            extra_ticket_data = {}

        # get proposal merge person if any is linked
        merge_person = None
        with contextlib.suppress(PersonMergeProposal.DoesNotExist):
            proposition_fusion = PersonMergeProposal.objects.get(original_person=candidate)
            merge_person = proposition_fusion.proposal_merge_person
            if noma:
                proposition_fusion.registration_id_sent_to_digit = noma
                proposition_fusion.save()

        person = merge_person if merge_person and _is_valid_merge_person(merge_person) else candidate

        addresses = candidate.personaddress_set.filter(label=PersonAddressType.RESIDENTIAL.name)

        ticket_response = _request_person_ticket_creation(person, noma, addresses, extra_ticket_data)

        logger.info(f"DIGIT Response: {ticket_response}")

        if ticket_response:
            PersonTicketCreation.objects.update_or_create(
                person=candidate,
                defaults={
                    'request_id': ticket_response['requestId'],
                    'status': ticket_response['status'],
                }
            )

    @classmethod
    def validate_person_ticket(cls, global_id: str):
        if not waffle.switch_is_active('fusion-digit') or global_id[0] not in TEMPORARY_ACCOUNT_GLOBAL_ID_PREFIX:
            return ValidationTicketResponseDTO(valid=True, errors=[])

        candidate = Person.objects.get(global_id=global_id)

        # get proposal merge person if any is linked
        merge_person = None
        proposition = PersonMergeProposal.objects.filter(original_person=candidate, proposal_merge_person__isnull=False)
        if proposition.exists():
            merge_person = proposition.get().proposal_merge_person

        person = merge_person if _is_valid_merge_person(merge_person) else candidate
        addresses = candidate.personaddress_set.filter(label=PersonAddressType.RESIDENTIAL.name)

        submitted_admission = candidate.baseadmission_set.all().filter(submitted_at__isnull=False).first()
        if not submitted_admission:
            logger.info(f"DIGIT validation canceled: no admission submitted for the candidate")
            return

        program_type = submitted_admission.training.education_group_type.name

        sap_number = cls._get_sap_number(candidate)
        if sap_number:
            logger.info(f"DIGIT retrieve SAP client number: {sap_number}")
            return

        ticket_response = _request_person_ticket_validation(person, addresses, program_type, sap_number)

        PersonMergeProposal.objects.update_or_create(
            original_person=candidate,
            defaults={
                "validation": ticket_response,
                "last_similarity_result_update": datetime.now()
            }
        )

        logger.info(f"DIGIT Response: {ticket_response}")

        return ValidationTicketResponseDTO(
            valid=ticket_response['valid'],
            errors=ticket_response['errors'],
        )

    @classmethod
    def _get_sap_number(cls, candidate):
        return candidate.sapclient_set.first().client_number if candidate.sapclient_set.first() else None

    @classmethod
    def get_person_ticket_status(cls, global_id: str) -> Optional[StatutTicketPersonneDTO]:
        if not waffle.switch_is_active('fusion-digit'):
            return None

        try:
            ticket = PersonTicketCreation.objects.select_related('person').get(person__global_id=global_id)
            return StatutTicketPersonneDTO(
                request_id=ticket.request_id,
                matricule=ticket.person.global_id,
                nom=ticket.person.last_name,
                noma=ticket.person.last_registration_id,
                prenom=ticket.person.first_name,
                statut=ticket.status,
                errors=[{'msg': error['msg'], 'code': error['errorCode']['errorCode']} for error in ticket.errors],
            )
        except PersonTicketCreation.DoesNotExist:
            return None

    @classmethod
    def retrieve_person_ticket_status_from_digit(cls, global_id: str) -> Optional[str]:
        if not waffle.switch_is_active('fusion-digit'):
            return None

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
        if not waffle.switch_is_active('fusion-digit'):
            return []

        tickets = PersonTicketCreation.objects.filter(
            ~Q(
                status__in=[
                    PersonTicketCreationStatus.DONE.value,
                    PersonTicketCreationStatus.DONE_WITH_WARNINGS.value,
                ]
            )
        ).select_related('person').values(
            'request_id', 'person__last_registration_id', 'person__last_name', 'person__first_name',
            'person__global_id', 'status', 'errors'
        )
        return [
            StatutTicketPersonneDTO(
                request_id=ticket['request_id'],
                matricule=ticket['person__global_id'],
                noma=ticket['person__last_registration_id'],
                nom=ticket['person__last_name'],
                prenom=ticket['person__first_name'],
                statut=ticket['status'],
                errors=[{'msg': error['msg'], 'code': error['errorCode']['errorCode']} for error in ticket['errors']],
            ) for ticket in tickets
        ]

    @classmethod
    def retrieve_list_error_merge_proposals(cls) -> List[PropositionFusionPersonneDTO]:
        person_merge_proposals = PersonMergeProposal.objects.filter(status=PersonMergeStatus.ERROR.name)
        return [
            PropositionFusionPersonneDTO(
                status=proposal.status,
                matricule=proposal.original_person.global_id,
                original_person_uuid=proposal.original_person.uuid,
                last_name=proposal.original_person.last_name,
                first_name=proposal.original_person.first_name,
                other_name=proposal.original_person.other_name,
                sex=proposal.original_person.sex,
                gender=proposal.original_person.gender,
                birth_date=proposal.original_person.birth_date,
                birth_country=proposal.original_person.birth_country,
                birth_place=proposal.original_person.birth_place,
                civil_state=proposal.original_person.civil_state,
                country_of_citizenship=proposal.original_person.country_of_citizenship.name
                if proposal.original_person.country_of_citizenship else None,
                national_number=proposal.original_person.national_number,
                id_card_number=proposal.original_person.id_card_number,
                passport_number=proposal.original_person.passport_number,
                id_card_expiry_date=proposal.original_person.id_card_expiry_date,
                professional_curex_uuids=proposal.professional_curex_to_merge,
                educational_curex_uuids=proposal.educational_curex_to_merge,
                validation=proposal.validation,
                last_registration_id=proposal.proposal_merge_person.last_registration_id,
            ) for proposal in person_merge_proposals
        ]

    @classmethod
    def get_global_id(cls, noma: str) -> str:
        if not waffle.switch_is_active('fusion-digit'):
            return ""

        if settings.MOCK_DIGIT_SERVICE_CALL:
            return "00000000"
        else:
            logger.info(f"DIGIT retrieve matricule from NOMA - {noma}")
            response = requests.get(
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': settings.ESB_AUTHORIZATION,
                },
                url=f"{settings.ESB_API_URL}/{settings.DIGIT_REQUEST_MATRICULE_URL}/{noma}"
            )
            matricule = response.json()['person']['matricule']
            return format_matricule(matricule)

    @classmethod
    def modifier_matricule_candidat(cls, candidate_global_id: str, digit_global_id: str):
        candidate = Person.objects.get(global_id=candidate_global_id)
        candidate.global_id = digit_global_id
        candidate.external_id = f"osis.person_{digit_global_id}"
        candidate.save()

    @classmethod
    def get_registration_id_sent_to_digit(cls, global_id: str) -> Optional[str]:
        candidate = Person.objects.get(global_id=global_id)
        if hasattr(candidate, 'personmergeproposal'):
            return candidate.personmergeproposal.registration_id_sent_to_digit or None
        else:
            return None

    @classmethod
    def has_pending_digit_creation_ticket(cls, global_id: str) -> bool:
        candidate = Person.objects.prefetch_related('personticketcreation_set').get(global_id=global_id)
        return any(t for t in candidate.personticketcreation_set.all() if t.status in [
            PersonTicketCreationStatus.CREATED.name,
            PersonTicketCreationStatus.DONE.name,
            PersonTicketCreationStatus.DONE_WITH_WARNINGS.name,
            PersonTicketCreationStatus.IN_PROGRESS.name,
        ])


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


def _request_person_ticket_creation(person: Person, noma: str, addresses: QuerySet, extra_ticket_data: dict):
    if settings.MOCK_DIGIT_SERVICE_CALL:
        return {"requestId": "1", "status": "CREATED"}
    else:
        ticket_data = json.dumps(_get_ticket_data(person, noma, addresses, **extra_ticket_data))
        logger.info(
            f"DIGIT sent data: {ticket_data}"
        )
        response = requests.post(
            headers={
                'Content-Type': 'application/json',
                'Authorization': settings.ESB_AUTHORIZATION,
            },
            data=ticket_data,
            url=f"{settings.ESB_API_URL}/{settings.DIGIT_ACCOUNT_CREATION_URL}"
        )
        return response.json()


def _request_person_ticket_validation(person: Person, addresses: QuerySet, program_type: str, sap_number: str):
    if settings.MOCK_DIGIT_SERVICE_CALL:
        return {"errors": [], "valid": True}
    else:
        logger.info(
            f"DIGIT sent data: {json.dumps(_get_ticket_data(person, '0', addresses, program_type, sap_number))}"
        )
        response = requests.post(
            headers={
                'Content-Type': 'application/json',
                'Authorization': settings.ESB_AUTHORIZATION,
            },
            data=json.dumps(_get_ticket_data(person, '0', addresses, program_type, sap_number)),
            url=f"{settings.ESB_API_URL}/{settings.DIGIT_ACCOUNT_VALIDATION_URL}"
        )
        return response.json()


def _get_ticket_data(person: Person, noma: str, addresses: QuerySet, program_type: str, sap_number: str):
    noma = person.last_registration_id if person.last_registration_id else noma
    if person.birth_date:
        birth_date = person.birth_date.strftime('%Y-%m-%d')
    elif person.birth_year:
        birth_date = f"{person.birth_year}-00-00"
    else:
        birth_date = None

    start_date_limit_idm = date(date.today().year, 6, 1)
    start_date_idm = date.today().strftime('%Y-%m-%d') if date.today() > start_date_limit_idm else start_date_limit_idm

    ticket_data = {
        "provider": {
            "source": "ETU",
            "sourceId": "".join(filter(str.isdigit, noma)),
            "actif": True,
        },
        "person": {
            "matricule": person.global_id,
            "lastName": person.last_name,
            "firstName": person.first_name,
            "birthDate": birth_date,
            "gender": "M" if person.gender == "H" else person.gender,
            "nationalRegister": "".join(filter(str.isdigit, person.national_number)),
            "nationality": person.country_of_citizenship.iso_code if person.country_of_citizenship else None,
            "otherFirstName": person.middle_name,
            "placeOfBirth": person.birth_place,
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
            }
            for address in addresses
        ],
        "activities": [
            {
                "idmId": _get_idm_number(program_type),
                "startDate": start_date_idm,
                "stopDate": "9999-12-31",
            }
        ],
        "physicalPerson": True,
    }

    if sap_number:
        ticket_data["applicationAccounts"] = {
            "source": "CLIETU",
            "sourceId": sap_number,
            "actif": True,
        }

    return ticket_data


def _is_valid_merge_person(person):
    return bool(person) and all([
        person.last_name,
        person.first_name,
        person.birth_date or person.birth_year,
        person.gender,
    ])


def _get_idm_number(program_type):
    return {
        "BACHELOR": 47,
        "MASTER_M1": 48,
        "MASTER_M4": 48,
        "MASTER_M5": 48,
        "MASTER_MA_120": 48,
        "MASTER_MD_120": 48,
        "MASTER_MS_120": 48,
        "MASTER_MA_180_240": 48,
        "MASTER_MD_180_240": 48,
        "MASTER_MS_180_240": 48,
        "AGGREGATION": 49,
        "MASTER_MC": 51,
        "FORMATION_PHD": 52,
        "PHD": 52,
        "CERTIFICATE": 54,
        "CAPAES": 55,
        "RESEARCH_CERTIFICATE": 57,
        "ISOLATED_CLASS": 58,
        "LANGUAGE_CLASS": 59,
        "JUNIOR_YEAR": 60,
        "CERTIFICATE_OF_PARTICIPATION": 61,
        "CERTIFICATE_OF_SUCCESS": 61,
        "CERTIFICATE_OF_HOLDING_CREDITS": 61,
        "UNIVERSITY_FIRST_CYCLE_CERTIFICATE": 61,
        "UNIVERSITY_SECOND_CYCLE_CERTIFICATE": 61
    }[program_type]
