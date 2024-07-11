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

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect
from waffle.testutils import override_switch

from admission.ddd.admission.commands import RechercherCompteExistantCommand, SoumettreTicketPersonneCommand
from backoffice.celery import app
from base.models.person import Person
from osis_common.ddd.interface import BusinessException

logger = logging.getLogger(settings.DEFAULT_LOGGER)


@app.task
@override_switch('fusion-digit', active=True)
def run(request=None, global_ids=None):
    candidates = Person.objects.prefetch_related('baseadmission_set').filter(~Q(baseadmissions=None))
    if global_ids:
        candidates = candidates.filter(global_id__in=global_ids)

    errors = []
    for candidate in candidates:
        if not candidate.baseadmission_set.all():
            errors.append(f"{candidate} - Candidate has no admission")

        for admission in candidate.baseadmission_set.all():
            if admission.determined_academic_year:
                logger.info(f'[DigIT] retrieve info from digit for {candidate}')
                from infrastructure.messages_bus import message_bus_instance
                message_bus_instance.invoke(RechercherCompteExistantCommand(
                    matricule=candidate.global_id,
                    nom=candidate.last_name,
                    prenom=candidate.first_name,
                    date_naissance=str(candidate.birth_date) if candidate.birth_date else "",
                    autres_prenoms=candidate.middle_name,
                    niss=candidate.national_number,
                    genre=candidate.sex,
                ))

                logger.info(f'[DigIT] send creation ticket for {candidate}')
                try:
                    message_bus_instance.invoke(SoumettreTicketPersonneCommand(
                        global_id=candidate.global_id,
                        annee=admission.determined_academic_year.year,
                    ))
                except BusinessException as e:
                    errors.append(str(e.message))
            else:
                errors.append(f"{candidate} - Candidate admission has not determined academic year")

    # Handle response when task is ran as a cmd from admin panel
    if request:
        for error in errors:
            messages.add_message(request, messages.ERROR, error)
        return redirect(request.META.get('HTTP_REFERER'))
