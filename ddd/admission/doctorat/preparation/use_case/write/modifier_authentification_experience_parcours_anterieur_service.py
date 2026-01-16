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
from admission.ddd.admission.doctorat.preparation.commands import (
    ModifierAuthentificationExperienceParcoursAnterieurCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import IHistorique
from admission.ddd.admission.doctorat.preparation.domain.service.i_notification import INotification
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.shared_kernel.domain.service.i_modifier_checklist_experience_parcours_anterieur import \
    IValidationExperienceParcoursAnterieurService
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import IPersonneConnueUclTranslator


def modifier_authentification_experience_parcours_anterieur(
    cmd: 'ModifierAuthentificationExperienceParcoursAnterieurCommand',
    proposition_repository: 'IPropositionRepository',
    notification: 'INotification',
    historique: 'IHistorique',
    personne_connue_ucl_translator: 'IPersonneConnueUclTranslator',
    validation_experience_parcours_anterieur_service: 'IValidationExperienceParcoursAnterieurService',
) -> 'PropositionIdentity':
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)

    proposition.specifier_authentification_experience_parcours_anterieur(
        auteur_modification=cmd.gestionnaire,
    )

    validation_experience_parcours_anterieur_service.modifier_authentification(
        matricule_candidat=proposition.matricule_candidat,
        uuid_experience=cmd.uuid_experience,
        type_experience=cmd.type_experience,
        etat_authentification=cmd.etat_authentification,
    )

    proposition_repository.save(proposition)

    gestionnaire_dto = personne_connue_ucl_translator.get(cmd.gestionnaire)

    message = notification.modifier_authentification_experience_parcours(
        proposition=proposition,
        etat_authentification=cmd.etat_authentification,
        gestionnaire=gestionnaire_dto,
    )

    historique.historiser_modification_authentification_experience_parcours(
        proposition=proposition,
        gestionnaire=gestionnaire_dto,
        etat_authentification=cmd.etat_authentification,
        message=message,
        uuid_experience=cmd.uuid_experience,
    )

    return proposition_id
