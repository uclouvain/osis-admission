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

from admission.ddd.admission.commands import RetrieveListePropositionFusionEnErreurQuery, \
    RechercherCompteExistantQuery
from admission.ddd.admission.dtos.proposition_fusion_personne import PropositionFusionPersonneDTO
from backoffice.celery import app

logger = logging.getLogger(settings.DEFAULT_LOGGER)


@app.task
def run():
    if not waffle.switch_is_active('fusion-digit'):
        logger.info("fusion-digit switch not active")
        return

    from infrastructure.messages_bus import message_bus_instance

    logger.info("Retry digit duplicates findings")

    # Retrieve list of proposals
    propositions_en_erreur: List[PropositionFusionPersonneDTO] = message_bus_instance.invoke(
        command=RetrieveListePropositionFusionEnErreurQuery()
    )

    logger.info("[ERROR MERGE PROPOSALS] : " + str(propositions_en_erreur))

    for proposition in propositions_en_erreur:
        message_bus_instance.invoke(
            command=RechercherCompteExistantQuery(
                matricule=proposition.matricule,
                nom=proposition.last_name,
                prenom=proposition.first_name,
                date_naissance=proposition.birth_date,
                autres_prenoms=proposition.other_name,
                niss=proposition.national_number,
                genre=proposition.sex,
            )
        )
