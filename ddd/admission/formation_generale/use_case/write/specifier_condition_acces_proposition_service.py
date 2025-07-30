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

from admission.ddd.admission.shared_kernel.repository.i_titre_acces_selectionnable import ITitreAccesSelectionnableRepository
from admission.ddd.admission.formation_generale.commands import SpecifierConditionAccesPropositionCommand
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from ddd.logic.shared_kernel.profil.domain.service.parcours_interne import IExperienceParcoursInterneTranslator


def specifier_condition_acces_proposition(
    cmd: 'SpecifierConditionAccesPropositionCommand',
    proposition_repository: 'IPropositionRepository',
    titre_acces_selectionnable_repository: 'ITitreAccesSelectionnableRepository',
    experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
) -> 'PropositionIdentity':
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)

    proposition.specifier_condition_acces(
        auteur_modification=cmd.gestionnaire,
        condition_acces=cmd.condition_acces,
        millesime_condition_acces=cmd.millesime_condition_acces,
        titre_acces_selectionnable_repository=titre_acces_selectionnable_repository,
        avec_complements_formation=cmd.avec_complements_formation,
        experience_parcours_interne_translator=experience_parcours_interne_translator,
    )

    proposition_repository.save(proposition)

    return proposition_id
