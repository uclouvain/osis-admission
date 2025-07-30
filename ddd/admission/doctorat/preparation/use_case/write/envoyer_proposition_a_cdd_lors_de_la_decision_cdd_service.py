# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.doctorat.preparation.commands import (
    EnvoyerPropositionACddLorsDeLaDecisionCddCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import IHistorique
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.shared_kernel.domain.model.proposition import PropositionIdentity


def envoyer_proposition_a_cdd_lors_de_la_decision_cdd(
    cmd: EnvoyerPropositionACddLorsDeLaDecisionCddCommand,
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
) -> PropositionIdentity:
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    proposition.soumettre_au_cdd_lors_de_la_decision_cdd(auteur_modification=cmd.gestionnaire)

    proposition_repository.save(entity=proposition)

    historique.historiser_envoi_cdd_par_sic_lors_de_la_decision_cdd(
        proposition=proposition,
        gestionnaire=cmd.gestionnaire,
    )

    return proposition.entity_id
