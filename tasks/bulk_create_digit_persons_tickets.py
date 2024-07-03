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
from django.db.models import Q
from django.shortcuts import redirect
from django.test import RequestFactory

from backoffice.celery import app
from base.models.person import Person
from django.test import Client

from base.models.person_merge_proposal import PersonMergeProposal

logger = logging.getLogger(settings.DEFAULT_LOGGER)


@app.task
def run(request=None):
    if not waffle.switch_is_active('fusion-digit'):
        logger.info("fusion-digit switch not active")
        return

    candidates = Person.objects.filter(~Q(baseadmissions=None))

    for candidate in candidates:
        for admission in candidate.baseadmission_set.all():
            if admission.determined_academic_year:
                if not hasattr(candidate, 'personmergeproposal'):
                    logger.info(f'[DigIT] retrieve info from digit for {candidate}')
                    url = f'/admissions/services/digit/search-account/{admission.uuid}'
                    Client().post(url)

                logger.info(f'[DigIT] send creation ticket for {candidate}')
                url = f'/admissions/services/digit/request-digit-person-creation/{admission.uuid}'
                Client().post(url)

    # Handle response when task is ran as a cmd from admin panel
    if request:
        return redirect(request.META.get('HTTP_REFERER'))
