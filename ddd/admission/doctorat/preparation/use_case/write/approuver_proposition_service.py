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
from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.commands import ApprouverPropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.avis import Avis
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import IHistorique
from admission.ddd.admission.doctorat.preparation.domain.service.i_notification import INotification
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository


def approuver_proposition(
    cmd: 'ApprouverPropositionCommand',
    proposition_repository: 'IPropositionRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    historique: 'IHistorique',
    notification: 'INotification',
) -> 'PropositionIdentity':
    # GIVEN
    entity_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=entity_id)
    statut_original_proposition = proposition.statut
    groupe_de_supervision = groupe_supervision_repository.get_by_proposition_id(entity_id)
    signataire = groupe_de_supervision.get_signataire(cmd.uuid_membre)
    groupe_de_supervision.verifier_promoteur_reference_renseigne_institut_these(
        signataire,
        groupe_de_supervision.promoteur_reference_id,
        proposition.projet.institut_these,
        cmd.institut_these,
    )
    avis = Avis.construire_approbation(cmd.commentaire_interne, cmd.commentaire_externe)

    # WHEN
    proposition.definir_institut_these(cmd.institut_these)
    groupe_de_supervision.approuver(signataire, cmd.commentaire_interne, cmd.commentaire_externe)

    # THEN
    proposition_repository.save(proposition)
    groupe_supervision_repository.save(groupe_de_supervision)
    historique.historiser_avis(proposition, signataire, avis, statut_original_proposition)
    notification.notifier_avis(proposition, signataire, avis)

    return proposition.entity_id
