# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.projet_doctoral.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.projet_doctoral.preparation.commands import DefinirCotutelleCommand
from admission.ddd.projet_doctoral.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.projet_doctoral.preparation.domain.service.i_historique import IHistorique
from admission.ddd.projet_doctoral.preparation.repository.i_groupe_de_supervision import IGroupeDeSupervisionRepository
from admission.ddd.projet_doctoral.preparation.repository.i_proposition import IPropositionRepository


def definir_cotutelle(
    cmd: 'DefinirCotutelleCommand',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(proposition_id)
    groupe_de_supervision = groupe_supervision_repository.get_by_proposition_id(proposition_id)

    # WHEN
    groupe_de_supervision.definir_cotutelle(
        motivation=cmd.motivation,
        institution_fwb=cmd.institution_fwb,
        institution=cmd.institution,
        demande_ouverture=cmd.demande_ouverture,
        convention=cmd.convention,
        autres_documents=cmd.autres_documents,
    )

    # THEN
    groupe_supervision_repository.save(groupe_de_supervision)
    historique.historiser_completion(proposition)

    return proposition_id
