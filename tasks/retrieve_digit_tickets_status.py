# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import logging
from typing import List

import waffle
from django.conf import settings
from django.db import transaction
from django.shortcuts import redirect
from waffle.testutils import override_switch

from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.commands import (
    RetrieveListeTicketsEnAttenteQuery,
    RetrieveAndStoreStatutTicketPersonneFromDigitCommand, FusionnerCandidatAvecPersonneExistanteCommand,
    RecupererMatriculeDigitQuery, ModifierMatriculeCandidatCommand,
)
from admission.ddd.admission.domain.validator.exceptions import PasDePropositionDeFusionEligibleException
from admission.ddd.admission.dtos.statut_ticket_personne import StatutTicketPersonneDTO
from admission.services.injection_epc.injection_signaletique import InjectionEPCSignaletique
from backoffice.celery import app
from base.models.person import Person
from base.models.person_creation_ticket import PersonTicketCreation, PersonTicketCreationStatus
from base.tasks import send_pictures_to_card_app

logger = logging.getLogger(settings.CELERY_EXCEPTION_LOGGER)


@app.task
def run(request=None):
    if not waffle.switch_is_active('fusion-digit'):
        logger.info("fusion-digit switch not active")
        return

    from infrastructure.messages_bus import message_bus_instance

    logger.info("Starting retrieve digit tickets status task")

    # Retrieve list of tickets
    tickets_pending = message_bus_instance.invoke(
        command=RetrieveListeTicketsEnAttenteQuery()
    )  # type: List[StatutTicketPersonneDTO]

    logger.info("[PENDING DIGIT TICKETS] : " + str(tickets_pending))

    for ticket in tickets_pending:
        status = message_bus_instance.invoke(
            command=RetrieveAndStoreStatutTicketPersonneFromDigitCommand(ticket_uuid=ticket.uuid)
        )
        logger.info(f"[DigIT Ticket] {ticket.nom}, {ticket.prenom}")
        logger.info(f"[DigIT Ticket status] {status}")

        if not Person.objects.filter(global_id=ticket.matricule).exists():
            logger.info(f"[DigIT Ticket] Only send signaletique to EPC because already traited")
            PersonTicketCreation.objects.filter(uuid=ticket.uuid).update(status=PersonTicketCreationStatus.CREATED.name)
            continue

        if status in ["DONE", "DONE_WITH_WARNINGS"]:
            try:
                _process_response_ticket(message_bus_instance, ticket)
            except PasDePropositionDeFusionEligibleException as e:
                logger.info(e.message)

    # Handle response when task is ran as a cmd from admin panel
    if request:
        return redirect(request.META.get('HTTP_REFERER'))


@transaction.atomic
def _process_response_ticket(message_bus_instance, ticket):
    from admission.infrastructure.admission.repository.digit import DigitRepository
    noma = DigitRepository.get_registration_id_sent_to_digit(global_id=ticket.matricule)

    digit_matricule = message_bus_instance.invoke(
        command=RecupererMatriculeDigitQuery(
            noma=noma,
        )
    )
    logger.info(f"[DigIT Ticket noma - matricule] NOMA: {noma} - MATR: {digit_matricule}")

    if Person.objects.filter(global_id=digit_matricule).exists():
        try:
            message_bus_instance.invoke(
                command=FusionnerCandidatAvecPersonneExistanteCommand(
                    candidate_global_id=digit_matricule,
                    ticket_uuid=ticket.uuid,
                )
            )
            logger.info(f"[DigIT Ticket merge with existing person]")
        except PasDePropositionDeFusionEligibleException:
            logger.info(f"[DigIT] Pas de proposition de fusion éligible. Fusion ignorée")
    else:
        message_bus_instance.invoke(
            command=ModifierMatriculeCandidatCommand(
                candidate_global_id=ticket.matricule,
                digit_global_id=digit_matricule,
                ticket_uuid=ticket.uuid,
            )
        )
        logger.info(f"[DigIT Ticket edit candidate global id]")

    logger.info("[DigIT Signaletique injection into EPC]")
    _injecter_signaletique_a_epc(digit_matricule)
    send_pictures_to_card_app.run.delay(global_id=digit_matricule)
    logger.info(f"[Send picture to card]")


def _injecter_signaletique_a_epc(matricule: str):
    demande = BaseAdmission.objects.filter(
        submitted_at__isnull=False,
        candidate__global_id=matricule,
    ).order_by('submitted_at').first()
    InjectionEPCSignaletique().injecter(admission=demande)


@override_switch('fusion-digit', active=True)
def force_run(request=None):
    return run(request=request)
