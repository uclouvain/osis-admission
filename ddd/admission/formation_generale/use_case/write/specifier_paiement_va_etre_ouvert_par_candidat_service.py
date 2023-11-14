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
from admission.ddd.admission.formation_generale.commands import (
    SpecifierPaiementVaEtreOuvertParCandidatCommand,
)
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.service.i_paiement_frais_dossier import IPaiementFraisDossier
from admission.ddd.admission.formation_generale.dtos.paiement import PaiementDTO
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository


def specifier_paiement_va_etre_ouvert_par_candidat(
    cmd: 'SpecifierPaiementVaEtreOuvertParCandidatCommand',
    proposition_repository: 'IPropositionRepository',
    paiement_frais_dossier_service: 'IPaiementFraisDossier',
) -> PaiementDTO:
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)

    # WHEN
    paiement_frais_dossier_service.verifier_paiement_frais_dossier_necessaire(
        proposition=proposition,
    )

    # THEN
    paiement_dto = paiement_frais_dossier_service.ouvrir_paiement(
        proposition_uuid=proposition.entity_id.uuid,
    )

    return paiement_dto
