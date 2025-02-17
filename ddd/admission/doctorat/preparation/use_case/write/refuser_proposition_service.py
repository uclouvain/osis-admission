# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.doctorat.preparation.commands import (
    RefuserPropositionCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.service.avis import Avis
from admission.ddd.admission.doctorat.preparation.domain.service.deverrouiller_projet_doctoral import (
    DeverrouillerPropositionProjetDoctoral,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import (
    IHistorique,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_notification import (
    INotification,
)
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import (
    IPropositionRepository,
)
from admission.ddd.admission.domain.service.i_raccrocher_experiences_curriculum import (
    IRaccrocherExperiencesCurriculum,
)


def refuser_proposition(
    cmd: 'RefuserPropositionCommand',
    proposition_repository: 'IPropositionRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    historique: 'IHistorique',
    notification: 'INotification',
    raccrocher_experiences_curriculum: 'IRaccrocherExperiencesCurriculum',
) -> 'PropositionIdentity':
    # GIVEN
    entity_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition_candidat = proposition_repository.get(entity_id=entity_id)
    statut_original_proposition = proposition_candidat.statut
    groupe_de_supervision = groupe_supervision_repository.get_by_proposition_id(entity_id)
    signataire_id = groupe_de_supervision.get_signataire(cmd.uuid_membre)
    avis = Avis.construire_refus(cmd.commentaire_interne, cmd.commentaire_externe, cmd.motif_refus)

    # WHEN
    groupe_de_supervision.refuser(signataire_id, cmd.commentaire_interne, cmd.commentaire_externe, cmd.motif_refus)
    DeverrouillerPropositionProjetDoctoral().deverrouiller_apres_refus(proposition_candidat, signataire_id)

    # THEN
    historique.historiser_avis(proposition_candidat, signataire_id, avis, statut_original_proposition)
    notification.notifier_avis(proposition_candidat, signataire_id, avis)
    groupe_supervision_repository.save(groupe_de_supervision)
    proposition_repository.save(proposition_candidat)
    raccrocher_experiences_curriculum.decrocher(proposition_candidat)

    return proposition_candidat.entity_id
