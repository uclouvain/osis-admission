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
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.commands import (
    ApprouverPropositionParFaculteCommand,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.ddd.admission.formation_generale.domain.service.i_historique import IHistorique
from admission.ddd.admission.formation_generale.domain.service.i_pdf_generation import IPDFGeneration
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository


def approuver_proposition_par_faculte(
    cmd: ApprouverPropositionParFaculteCommand,
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
    pdf_generation: 'IPDFGeneration',
) -> PropositionIdentity:
    # GIVEN
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    # WHEN
    Checklist.verifier_fac_peut_donner_decision_acceptation(proposition=proposition)

    proposition.approuver_par_fac()

    # THEN
    pdf_generation.generer_attestation_accord_facultaire(proposition=proposition, gestionnaire=cmd.gestionnaire)

    proposition_repository.save(entity=proposition)

    historique.historiser_acceptation_fac(proposition=proposition, gestionnaire=cmd.gestionnaire)

    return proposition.entity_id
