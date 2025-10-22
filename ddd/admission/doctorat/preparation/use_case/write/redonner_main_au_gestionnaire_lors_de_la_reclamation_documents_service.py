# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from typing import Any

from admission.ddd.admission.doctorat.preparation.commands import (
    RecupererDocumentsReclamesPropositionQuery,
    RedonnerMainAuGestionnaireLorsDeLaReclamationDocumentsCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import (
    IPropositionRepository,
)
from admission.ddd.admission.shared_kernel.domain.service.i_historique import (
    IHistorique,
)
from admission.ddd.admission.shared_kernel.domain.validator.validator_by_business_action import (
    RendreMainGestionnaireLorsReclamationDocumentsValidatorList,
)


def redonner_main_au_gestionnaire_lors_de_la_reclamation_documents(
    msg_bus: Any,
    cmd: 'RedonnerMainAuGestionnaireLorsDeLaReclamationDocumentsCommand',
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
) -> PropositionIdentity:
    # GIVEN
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    documents_reclames = msg_bus.invoke(
        RecupererDocumentsReclamesPropositionQuery(uuid_proposition=cmd.uuid_proposition)
    )

    # WHEN
    RendreMainGestionnaireLorsReclamationDocumentsValidatorList(
        documents_reclames=documents_reclames,
    ).validate()

    proposition.completer_documents_par_candidat()

    # THEN
    proposition_repository.save(proposition)

    historique.historiser_renvoi_demande_au_gestionnaire_par_candidat_lors_de_la_reclamation_documents(
        proposition=proposition,
    )

    return proposition.entity_id
