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
from admission.ddd.admission.projet_doctoral.preparation.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.projet_doctoral.preparation.commands import IdentifierPromoteurCommand
from admission.ddd.admission.projet_doctoral.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.projet_doctoral.preparation.domain.service.i_historique import IHistorique
from admission.ddd.admission.projet_doctoral.preparation.domain.service.i_promoteur import IPromoteurTranslator
from admission.ddd.admission.projet_doctoral.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.projet_doctoral.preparation.repository.i_proposition import IPropositionRepository


def identifier_promoteur(
    cmd: 'IdentifierPromoteurCommand',
    proposition_repository: 'IPropositionRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    promoteur_translator: 'IPromoteurTranslator',
    historique: 'IHistorique',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    groupe_de_supervision = groupe_supervision_repository.get_by_proposition_id(proposition_id)
    proposition = proposition_repository.get(proposition_id)
    promoteur_id = promoteur_translator.get(cmd.matricule)

    # WHEN
    groupe_de_supervision.identifier_promoteur(promoteur_id)

    # THEN
    groupe_supervision_repository.save(groupe_de_supervision)
    historique.historiser_ajout_membre(proposition, groupe_de_supervision, promoteur_id)

    return proposition_id
