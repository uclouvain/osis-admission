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
from django.db.models import Q
from django.shortcuts import redirect
from waffle.testutils import override_switch

from admission.contrib.models import GeneralEducationAdmission
from admission.ddd.admission.commands import (
    RetrieveListeTicketsEnAttenteQuery,
    RetrieveAndStoreStatutTicketPersonneFromDigitCommand, FusionnerCandidatAvecPersonneExistanteCommand,
    RecupererMatriculeDigitQuery, ModifierMatriculeCandidatCommand,
)
from admission.ddd.admission.domain.validator.exceptions import PasDePropositionDeFusionEligibleException
from admission.ddd.admission.dtos.statut_ticket_personne import StatutTicketPersonneDTO
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from backoffice.celery import app
from base.models.person import Person
from base.models.person_creation_ticket import PersonTicketCreation, PersonTicketCreationStatus
from base.tasks import send_pictures_to_card_app

logger = logging.getLogger(settings.CELERY_EXCEPTION_LOGGER)

PREFIX_TASK = "[Retrieve DigIT ticket status] :"


@app.task
@transaction.non_atomic_requests
def run(request=None):
    if not waffle.switch_is_active('fusion-digit'):
        logger.info(f"{PREFIX_TASK} fusion-digit switch not active")
        return

    from infrastructure.messages_bus import message_bus_instance
    logger.info(f"{PREFIX_TASK} starting task...")

    # Retrieve list of tickets
    logger.info(f"{PREFIX_TASK} fetch pending DigIT tickets...")
    tickets_pending = message_bus_instance.invoke(RetrieveListeTicketsEnAttenteQuery())  # type: List[StatutTicketPersonneDTO]
    logger.info(f"{PREFIX_TASK} pending DigIT tickets..." + str(tickets_pending))

    for ticket in tickets_pending:
        try:
            with transaction.atomic():
                status = message_bus_instance.invoke(
                    RetrieveAndStoreStatutTicketPersonneFromDigitCommand(ticket_uuid=ticket.uuid)
                )
                logger.info(f"{PREFIX_TASK} process DigIT ticket ({str(ticket)}")

                if not Person.objects.filter(global_id=ticket.matricule).exists():
                    logger.info(f"{PREFIX_TASK} matricule not found into database. Already processed ?")
                    continue

                if status in ["DONE", "DONE_WITH_WARNINGS"]:
                    try:
                        _process_successful_response_ticket(message_bus_instance, ticket)
                    except PasDePropositionDeFusionEligibleException as e:
                        logger.info(f"{PREFIX_TASK} {e.message}")
                else:
                    logger.info(f"{PREFIX_TASK} ticket in status {status}. No processing ticket response.")
        except Exception as e:
            logger.info(f"{PREFIX_TASK} An error occured during processing ticket ({repr(e)})")
            PersonTicketCreation.objects.filter(uuid=ticket.uuid).update(
                status=PersonTicketCreationStatus.ERROR.name,
                errors=[{"errorCode": {"errorCode": "ERROR_DURING_RETRIEVE_DIGIT_TICKET"}, 'msg': repr(e)}]
            )

    # Handle response when task is ran as a cmd from admin panel
    if request:
        return redirect(request.META.get('HTTP_REFERER'))


def _process_successful_response_ticket(message_bus_instance, ticket):
    from admission.infrastructure.admission.repository.digit import DigitRepository
    noma = DigitRepository.get_registration_id_sent_to_digit(global_id=ticket.matricule)

    logger.info(f"{PREFIX_TASK} fetch matricule DigIT from noma (NOMA: {noma})")
    digit_matricule = message_bus_instance.invoke(RecupererMatriculeDigitQuery(noma=noma))
    logger.info(f"{PREFIX_TASK} matricule DigIT found ({digit_matricule}) for noma ({noma})")

    if Person.objects.filter(global_id=digit_matricule).exists():
        try:
            message_bus_instance.invoke(
                FusionnerCandidatAvecPersonneExistanteCommand(
                    candidate_global_id=digit_matricule,
                    ticket_uuid=ticket.uuid,
                )
            )
            logger.info(f"{PREFIX_TASK} merge candidate with existing person data")
        except PasDePropositionDeFusionEligibleException:
            logger.info(f"{PREFIX_TASK} no merge candidate eligible. Merge abort")
    else:
        message_bus_instance.invoke(
            ModifierMatriculeCandidatCommand(
                candidate_global_id=ticket.matricule,
                digit_global_id=digit_matricule,
                ticket_uuid=ticket.uuid,
            )
        )
        logger.info(f"{PREFIX_TASK} "
                    f"edit candidate global_id ({ticket.matricule}) to set as internal account ({digit_matricule})")

    logger.info(f"{PREFIX_TASK} send signaletique into EPC")
    _injecter_signaletique_a_epc(digit_matricule)
    if settings.USE_CELERY:
        send_pictures_to_card_app.run.delay(global_id=digit_matricule)
    logger.info(f"{PREFIX_TASK} send picture to card")


def _injecter_signaletique_a_epc(matricule: str):
    from admission.services.injection_epc.injection_signaletique import InjectionEPCSignaletique

    # TODO: Inject also for other admisison type
    demande = GeneralEducationAdmission.objects.filter(
        candidate__global_id=matricule,
    ).filter(
        Q(
            type_demande=TypeDemande.ADMISSION.name,
            status=ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name
        )
        | Q(type_demande=TypeDemande.INSCRIPTION.name)
    ).order_by('created_at').first()
    InjectionEPCSignaletique().injecter(admission=demande)


@override_switch('fusion-digit', active=True)
@transaction.non_atomic_requests
def force_run(request=None):
    return run(request=request)
