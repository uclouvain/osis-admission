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
from django.shortcuts import redirect

from admission.ddd.admission.commands import RetrieveListeTicketsEnAttenteQuery, \
    RetrieveAndStoreStatutTicketPersonneFromDigitCommand, FusionnerCandidatAvecPersonneExistanteCommand, \
    RecupererMatriculeDigitQuery, ModifierMatriculeCandidatCommand
from backoffice.celery import app


@app.task
def run(request=None):
    from infrastructure.messages_bus import message_bus_instance

    # Retrieve list of tickets
    tickets_pending = message_bus_instance.invoke(command=RetrieveListeTicketsEnAttenteQuery())

    for ticket in tickets_pending:
        status = message_bus_instance.invoke(
            command=RetrieveAndStoreStatutTicketPersonneFromDigitCommand(global_id=ticket.matricule)
        )

        if status in ["DONE", "DONE_WITH_WARNINGS"]:
            digit_matricule = message_bus_instance.invoke(
                command=RecupererMatriculeDigitQuery(
                    noma=ticket.noma,
                )
            )
            if digit_matricule == ticket.matricule:
                message_bus_instance.invoke(
                    command=FusionnerCandidatAvecPersonneExistanteCommand(
                        candidate_global_id=digit_matricule,
                    )
                )
            else:
                message_bus_instance.invoke(
                    command=ModifierMatriculeCandidatCommand(
                        candidate_global_id=ticket.matricule,
                        digit_global_id=digit_matricule
                    )
                )


    # Handle response when task is ran as a cmd from admin panel
    if request:
        return redirect(request.META.get('HTTP_REFERER'))
