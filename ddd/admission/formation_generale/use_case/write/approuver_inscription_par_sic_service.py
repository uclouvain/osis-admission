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
from admission.ddd.admission.formation_generale.commands import (
    ApprouverInscriptionParSicCommand,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.i_historique import IHistorique
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository


def approuver_inscription_par_sic(
    cmd: ApprouverInscriptionParSicCommand,
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
) -> PropositionIdentity:
    # GIVEN
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    # WHEN
    proposition.approuver_par_sic(auteur_modification=cmd.auteur)

    # THEN
    proposition_repository.save(entity=proposition)

    historique.historiser_acceptation_sic(
        proposition=proposition,
        gestionnaire=cmd.auteur,
    )

    return proposition.entity_id
