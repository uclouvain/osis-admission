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
from admission.ddd.admission.formation_continue.commands import (
    ValiderPropositionCommand,
)
from admission.ddd.admission.formation_continue.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.formation_continue.domain.service.i_historique import (
    IHistorique,
)
from admission.ddd.admission.formation_continue.domain.service.i_notification import (
    INotification,
)
from admission.ddd.admission.formation_continue.events import (
    PropositionFormationContinueValideeEvent,
)
from admission.ddd.admission.formation_continue.repository.i_proposition import (
    IPropositionRepository,
)


def valider_proposition(
    msg_bus,
    cmd: 'ValiderPropositionCommand',
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
    profil_candidat_translator: 'IProfilCandidatTranslator',
) -> 'PropositionIdentity':
    # GIVEN
    proposition = proposition_repository.get(PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition))

    # WHEN
    proposition.approuver_proposition(
        gestionnaire=cmd.gestionnaire,
        profil_candidat_translator=profil_candidat_translator,
    )

    # THEN
    proposition_repository.save(proposition)
    historique.historiser_approuver_proposition(
        proposition=proposition,
        gestionnaire=cmd.gestionnaire,
    )

    msg_bus.publish(
        PropositionFormationContinueValideeEvent(
            entity_id=proposition.entity_id,
            matricule=proposition.matricule_candidat,
        )
    )

    return proposition.entity_id
