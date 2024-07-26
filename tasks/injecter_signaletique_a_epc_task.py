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
import json
import logging
from datetime import datetime
from typing import List

from django.conf import settings
from django.db import transaction

from admission.models.epc_injection import EPCInjectionType, EPCInjection, EPCInjectionStatus
from backoffice.celery import app as celery_app

logger = logging.getLogger(settings.CELERY_EXCEPTION_LOGGER)

PREFIX_TASK = "[Injecter signaletique vers EPC] :"


@celery_app.task
@transaction.non_atomic_requests
def run(admissions_references: List[str] = None):  # pragma: no cover
    from admission.services.injection_epc.injection_signaletique import InjectionEPCSignaletique

    epc_injections_signaletique_to_send = EPCInjection.objects.filter(
        type=EPCInjectionType.SIGNALETIQUE.name,
    ).exclude(status=EPCInjectionStatus.OK.name)
    if admissions_references is not None:
        epc_injections_signaletique_to_send = epc_injections_signaletique_to_send.filter(
            admission__reference__in=admissions_references,
        )

    logger.info(
        f"{PREFIX_TASK} Lancement des injections vers EPC de la signaletique dans la queue "
        f"(nbre: {epc_injections_signaletique_to_send.count()}) "
    )
    for epc_injection_signaletique in epc_injections_signaletique_to_send:
        with transaction.atomic():
            try:
                logger.info(
                    f"{PREFIX_TASK} Injection vers EPC de la signaletique dans la queue. "
                    f"{json.dumps(epc_injection_signaletique.payload, indent=4)}"
                )
                InjectionEPCSignaletique().envoyer_signaletique_dans_queue(
                    donnees=epc_injection_signaletique.payload,
                    admission_reference=str(epc_injection_signaletique.admission)
                )
                epc_injection_signaletique.status = EPCInjectionStatus.PENDING.name
            except Exception as e:
                logger.info(
                    f"{PREFIX_TASK} Une erreur est survenue lors de l'injection "
                    f"vers EPC de la signaletique de la demande avec reference "
                    f"{str(epc_injection_signaletique.admission)}"
                    f"(Cause: {repr(e)})"
                )
                epc_injection_signaletique.status = EPCInjectionStatus.OSIS_ERROR.name
            finally:
                epc_injection_signaletique.last_attempt_date = datetime.now()
                epc_injection_signaletique.save()
    logger.info(f"{PREFIX_TASK} Fin des injections vers EPC de la signaletique dans la queue ")
