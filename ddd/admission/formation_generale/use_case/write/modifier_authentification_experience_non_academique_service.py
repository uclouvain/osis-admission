# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.formation_generale.commands import ModifierAuthentificationExperienceNonAcademiqueCommand
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.i_historique import IHistorique
from admission.ddd.admission.formation_generale.domain.service.i_notification import INotification
from admission.ddd.admission.shared_kernel.domain.service.i_modifier_checklist_experience_parcours_anterieur import (
    IValidationExperienceParcoursAnterieurService,
)


def modifier_authentification_experience_non_academique(
    cmd: 'ModifierAuthentificationExperienceNonAcademiqueCommand',
    notification: 'INotification',
    historique: 'IHistorique',
    validation_experience_parcours_anterieur_service: 'IValidationExperienceParcoursAnterieurService',
) -> 'PropositionIdentity':
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)

    validation_experience_parcours_anterieur_service.modifier_authentification_experience_non_academique(
        uuid_experience=cmd.uuid_experience,
        etat_authentification=cmd.etat_authentification,
    )

    message = notification.modifier_authentification_experience_parcours(
        proposition_id=proposition_id,
        etat_authentification=cmd.etat_authentification,
    )

    historique.historiser_modification_authentification_experience_parcours(
        proposition_id=proposition_id,
        gestionnaire=cmd.gestionnaire,
        etat_authentification=cmd.etat_authentification,
        message=message,
        uuid_experience=cmd.uuid_experience,
    )

    return proposition_id
