# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.profil_candidat import ProfilCandidat
from admission.ddd.admission.formation_generale.commands import (
    VerifierCurriculumApresSoumissionQuery,
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
from ddd.logic.shared_kernel.profil.domain.service.parcours_interne import (
    IExperienceParcoursInterneTranslator,
)


def verifier_curriculum_apres_soumission(
    cmd: 'VerifierCurriculumApresSoumissionQuery',
    proposition_repository: 'IPropositionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    experience_parcours_interne_translator: 'IExperienceParcoursInterneTranslator',
    formation_translator: 'IFormationGeneraleTranslator',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)

    formation = formation_translator.get(entity_id=proposition.formation_id)

    # WHEN
    ProfilCandidat.verifier_curriculum_formation_generale_apres_soumission(
        proposition=proposition,
        profil_candidat_translator=profil_candidat_translator,
        experience_parcours_interne_translator=experience_parcours_interne_translator,
        verification_experiences_completees=True,
        grade_academique_formation_proposition=formation.grade_academique,
    )

    # THEN
    return proposition_id
