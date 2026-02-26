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
from itertools import chain
from typing import Union

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition as PropositionDoctorale,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import (
    Proposition as PropositionContinue,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    Proposition as PropositionGenerale,
)
from admission.ddd.admission.shared_kernel.domain.service.i_raccrocher_experiences_curriculum import (
    IRaccrocherExperiencesCurriculum,
)
from admission.infrastructure.admission.shared_kernel.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
)


class RaccrocherExperiencesCurriculumInMemory(IRaccrocherExperiencesCurriculum):
    @classmethod
    def raccrocher(
        cls,
        proposition: Union[PropositionContinue, PropositionDoctorale, PropositionGenerale],
    ):
        for xp in chain(
            ProfilCandidatInMemoryTranslator.experiences_academiques,
            ProfilCandidatInMemoryTranslator.experiences_non_academiques,
        ):
            if xp.personne == proposition.matricule_candidat:
                if xp.uuid not in ProfilCandidatInMemoryTranslator.valorisations:
                    ProfilCandidatInMemoryTranslator.valorisations[xp.uuid] = [proposition.entity_id.uuid]
                elif proposition.entity_id.uuid not in ProfilCandidatInMemoryTranslator.valorisations[xp.uuid]:
                    ProfilCandidatInMemoryTranslator.valorisations[xp.uuid].append(proposition.entity_id.uuid)

    @classmethod
    def decrocher(
        cls,
        proposition: Union[PropositionContinue, PropositionDoctorale, PropositionGenerale],
    ):
        for xp in chain(
            ProfilCandidatInMemoryTranslator.experiences_academiques,
            ProfilCandidatInMemoryTranslator.experiences_non_academiques,
        ):
            if xp.personne == proposition.matricule_candidat and ProfilCandidatInMemoryTranslator.valorisations.get(
                xp.uuid
            ):
                ProfilCandidatInMemoryTranslator.valorisations[xp.uuid].remove(proposition.entity_id.uuid)
