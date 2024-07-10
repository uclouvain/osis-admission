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

import waffle
from django.conf import settings
from django.shortcuts import redirect
from waffle.testutils import override_switch

from admission.ddd.admission.commands import RetrieveListeTicketsEnAttenteQuery, \
    RetrieveAndStoreStatutTicketPersonneFromDigitCommand, FusionnerCandidatAvecPersonneExistanteCommand, \
    RecupererMatriculeDigitQuery, ModifierMatriculeCandidatCommand
from backoffice.celery import app
from base.models.person import Person
from base.tasks import send_pictures_to_card_app

logger = logging.getLogger(settings.DEFAULT_LOGGER)


@app.task
def run(request=None):
    if not waffle.switch_is_active('fusion-digit'):
        logger.info("fusion-digit switch not active")
        return

    from infrastructure.messages_bus import message_bus_instance

    logger.info("Starting retrieve digit tickets status task")

    # Retrieve list of tickets
    tickets_pending = message_bus_instance.invoke(command=RetrieveListeTicketsEnAttenteQuery())

    logger.info("[PENDING DIGIT TICKETS] : " + str(tickets_pending))

    for ticket in tickets_pending:
        status = message_bus_instance.invoke(
            command=RetrieveAndStoreStatutTicketPersonneFromDigitCommand(global_id=ticket.matricule)
        )

        logger.info(f"[DigIT Ticket] {ticket.nom}, {ticket.prenom}")
        logger.info(f"[DigIT Ticket status] {status}")

        person = Person.objects.get(global_id=ticket.matricule)
        noma = person.personmergeproposal.registration_id_sent_to_digit

        if status in ["DONE", "DONE_WITH_WARNINGS"] and noma:
            digit_matricule = message_bus_instance.invoke(
                command=RecupererMatriculeDigitQuery(
                    noma=noma,
                )
            )
            logger.info(f"[DigIT Ticket noma - matricule] NOMA: {ticket.noma} - MATR: {digit_matricule}")

            if Person.objects.filter(global_id=digit_matricule).exists():
                message_bus_instance.invoke(
                    command=FusionnerCandidatAvecPersonneExistanteCommand(
                        candidate_global_id=digit_matricule,
                    )
                )
                logger.info(f"[DigIT Ticket merge with existing person]")
            else:
                message_bus_instance.invoke(
                    command=ModifierMatriculeCandidatCommand(
                        candidate_global_id=ticket.matricule,
                        digit_global_id=digit_matricule
                    )
                )
                logger.info(f"[DigIT Ticket edit candidate global id]")

            send_pictures_to_card_app.run.delay(global_id=digit_matricule)
            logger.info(f"[DigIT Ticket edit candidate global id]")

    # Handle response when task is ran as a cmd from admin panel
    if request:
        return redirect(request.META.get('HTTP_REFERER'))


@override_switch('fusion-digit', active=True)
def force_run(request=None):
    return run(request=request)
