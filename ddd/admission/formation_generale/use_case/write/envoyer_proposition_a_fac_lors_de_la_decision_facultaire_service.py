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
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.commands import EnvoyerPropositionAFacLorsDeLaDecisionFacultaireCommand
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.i_historique import IHistorique
from admission.ddd.admission.formation_generale.domain.service.i_notification import INotification
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository


def envoyer_proposition_a_fac_lors_de_la_decision_facultaire(
    cmd: EnvoyerPropositionAFacLorsDeLaDecisionFacultaireCommand,
    proposition_repository: 'IPropositionRepository',
    notification: 'INotification',
    historique: 'IHistorique',
) -> PropositionIdentity:
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    proposition.soumettre_a_fac_lors_de_la_decision_facultaire(auteur_modification=cmd.gestionnaire)

    proposition_repository.save(entity=proposition)

    message = notification.confirmer_envoi_a_fac_lors_de_la_decision_facultaire(proposition=proposition)

    historique.historiser_envoi_fac_par_sic_lors_de_la_decision_facultaire(
        proposition=proposition,
        message=message,
        gestionnaire=cmd.gestionnaire,
    )

    return proposition.entity_id
