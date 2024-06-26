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

from admission.ddd.admission.domain.repository.i_titre_acces_selectionnable import ITitreAccesSelectionnableRepository
from admission.ddd.admission.formation_generale.commands import ModifierStatutChecklistParcoursAnterieurCommand
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from ddd.logic.shared_kernel.profil.domain.service.i_parcours_interne import IExperienceParcoursInterneTranslator


def modifier_statut_checklist_parcours_anterieur(
    cmd: 'ModifierStatutChecklistParcoursAnterieurCommand',
    proposition_repository: 'IPropositionRepository',
    titre_acces_selectionnable_repository: 'ITitreAccesSelectionnableRepository',
    experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
) -> 'PropositionIdentity':
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)

    titres_acces_selectionnes = titre_acces_selectionnable_repository.search_by_proposition(
        proposition_identity=proposition_id,
        experience_parcours_interne_translator=experience_parcours_interne_translator,
        seulement_selectionnes=True,
    )

    proposition.specifier_statut_checklist_parcours_anterieur(
        statut_checklist_cible=cmd.statut,
        titres_acces_selectionnes=titres_acces_selectionnes,
        auteur_modification=cmd.gestionnaire,
    )

    proposition_repository.save(proposition)

    return proposition_id
