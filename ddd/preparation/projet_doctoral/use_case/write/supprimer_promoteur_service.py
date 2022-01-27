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
from admission.ddd.preparation.projet_doctoral.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.preparation.projet_doctoral.commands import SupprimerPromoteurCommand
from admission.ddd.preparation.projet_doctoral.domain.model.proposition import PropositionIdentity
from admission.ddd.preparation.projet_doctoral.repository.i_groupe_de_supervision import IGroupeDeSupervisionRepository
from admission.ddd.preparation.projet_doctoral.repository.i_proposition import IPropositionRepository


def supprimer_promoteur(
        cmd: 'SupprimerPromoteurCommand',
        proposition_repository: 'IPropositionRepository',
        groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition_candidat = proposition_repository.get(entity_id=proposition_id)
    groupe_supervision = groupe_supervision_repository.get_by_proposition_id(proposition_id)
    promoteur_id = groupe_supervision.get_promoteur(cmd.matricule)

    # WHEN
    groupe_supervision.supprimer_promoteur(promoteur_id)

    # THEN
    groupe_supervision_repository.save(groupe_supervision)

    return proposition_id
