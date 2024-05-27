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
from admission.ddd.admission.domain.repository.i_titre_acces_selectionnable import ITitreAccesSelectionnableRepository
from admission.ddd.admission.formation_generale.commands import (
    ApprouverInscriptionTardiveParFaculteCommand,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.i_historique import IHistorique
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import IPersonneConnueUclTranslator


def approuver_inscription_tardive_par_faculte(
    cmd: ApprouverInscriptionTardiveParFaculteCommand,
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
    personne_connue_ucl_translator: 'IPersonneConnueUclTranslator',
    titre_acces_selectionnable_repository: 'ITitreAccesSelectionnableRepository',
) -> PropositionIdentity:
    # GIVEN
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    gestionnaire_dto = personne_connue_ucl_translator.get(cmd.gestionnaire)

    titres_selectionnes = titre_acces_selectionnable_repository.search_by_proposition(
        proposition_identity=proposition.entity_id,
        seulement_selectionnes=True,
    )

    # WHEN
    proposition.approuver_inscription_tardive_par_fac(
        auteur_modification=cmd.gestionnaire,
        titres_selectionnes=titres_selectionnes,
    )

    # THEN
    proposition_repository.save(entity=proposition)

    historique.historiser_acceptation_fac(proposition=proposition, gestionnaire=gestionnaire_dto)

    return proposition.entity_id
