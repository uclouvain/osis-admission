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
from admission.ddd.admission.formation_generale.commands import (
    ModifierStatutChecklistExperienceAcademiqueCommand,
)
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.formation_generale.domain.service.i_formation import (
    IFormationGeneraleTranslator,
)
from admission.ddd.admission.formation_generale.repository.i_proposition import (
    IPropositionRepository,
)
from admission.ddd.admission.shared_kernel.domain.service.i_modifier_checklist_experience_parcours_anterieur import (
    IValidationExperienceParcoursAnterieurService,
)
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)


def modifier_statut_checklist_experience_academique(
    cmd: 'ModifierStatutChecklistExperienceAcademiqueCommand',
    proposition_repository: 'IPropositionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    formation_translator: 'IFormationGeneraleTranslator',
    validation_experience_parcours_anterieur_service: 'IValidationExperienceParcoursAnterieurService',
) -> 'PropositionIdentity':
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)

    formation = formation_translator.get(entity_id=proposition.formation_id)

    validation_experience_parcours_anterieur_service.modifier_statut_experience_academique(
        proposition_id=proposition_id,
        matricule_candidat=proposition.matricule_candidat,
        uuid_experience=cmd.uuid_experience,
        statut=cmd.statut,
        profil_candidat_translator=profil_candidat_translator,
        grade_academique_formation_proposition=formation.grade_academique,
    )

    return proposition_id
