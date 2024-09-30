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
from django.db.models import Q

from admission.auth.predicates.general import payment_needed_after_submission, payment_needed_after_manager_request
from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.online_payment import PaymentStatus
from admission.ddd.admission.formation_generale.commands import (
    PayerFraisDossierPropositionSuiteDemandeCommand,
    PayerFraisDossierPropositionSuiteSoumissionCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.services.paiement_en_ligne import PaiementEnLigneService
from backoffice.celery import app as celery_app
from infrastructure.messages_bus import message_bus_instance

logger = logging.getLogger(settings.CELERY_EXCEPTION_LOGGER)

TASK_PREFIX = "[Verification Paiements]"

@celery_app.task
def run():  # pragma: no cover
    admissions_en_defaut_de_paiement = BaseAdmission.objects.filter(
        Q(generaleducationadmission__status=ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name)
        | Q(checklist__current__frais_dossier__statut=ChoixStatutChecklist.GEST_BLOCAGE.name)
    )
    logger.info(
        f"{TASK_PREFIX} Verification des paiements pour {admissions_en_defaut_de_paiement.count()} dossiers"
    )
    for admission in admissions_en_defaut_de_paiement:
        paiements = PaiementEnLigneService.get_all_payments(admission)
        logger.info(f"{TASK_PREFIX} > Verification du paiement pour le dossier {str(admission)}")
        if paiements.filter(status=PaymentStatus.PAID.name).exists():
            logger.info(f"{TASK_PREFIX}  > Paiement effectue ({str(admission)}) => Mise a jour de la demande")
            # Update the admission and inform the candidate that the payment is successful
            if payment_needed_after_submission(admission=admission):
                logger.info(f"{TASK_PREFIX}   > Paiement suite a soumission de la demande ({str(admission)})")
                # After the submission
                message_bus_instance.invoke(
                    PayerFraisDossierPropositionSuiteSoumissionCommand(uuid_proposition=admission.uuid)
                )
            elif payment_needed_after_manager_request(admission=admission):
                logger.info(f"{TASK_PREFIX}   > Paiement suite a requete du gestionnaire ({str(admission)})")
                # After a manager request
                message_bus_instance.invoke(
                    PayerFraisDossierPropositionSuiteDemandeCommand(uuid_proposition=admission.uuid)
                )
            else:
                logger.info(f"{TASK_PREFIX}   > Technical issue (ne passe pas dans les if/elif) ({str(admission)})")
        else:
            logger.info(f"{TASK_PREFIX}  > Paiement non effectue ({str(admission)})")
