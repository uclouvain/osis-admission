# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.formation_generale.domain.service.i_historique import IHistorique
from admission.ddd.admission.formation_generale.domain.service.i_paiement_frais_dossier import IPaiementFraisDossier
from admission.ddd.admission.formation_generale.commands import SpecifierPaiementPlusNecessaireCommand
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository


def specifier_paiement_plus_necessaire(
    cmd: 'SpecifierPaiementPlusNecessaireCommand',
    proposition_repository: 'IPropositionRepository',
    paiement_frais_dossier_service: 'IPaiementFraisDossier',
    historique: 'IHistorique',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)
    statut_initial = proposition.statut

    # WHEN
    paiement_frais_dossier_service.verifier_paiement_non_realise(
        proposition=proposition,
    )

    # THEN
    proposition.specifier_paiement_frais_dossier_plus_necessaire_par_gestionnaire(
        statut_checklist_cible=cmd.statut_checklist_frais_dossier,
    )
    proposition_repository.save(proposition)

    historique.historiser_annulation_demande_paiement_par_gestionnaire(proposition, cmd.gestionnaire, statut_initial)

    return proposition_id
