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

from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.formation_continue.commands import InitierPropositionCommand
from admission.ddd.admission.formation_continue.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixMoyensDecouverteFormation
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition
from admission.ddd.admission.formation_continue.repository.i_proposition import IPropositionRepository
from osis_common.ddd import interface


class PropositionBuilder(interface.RootEntityBuilder):
    @classmethod
    def build_from_repository_dto(cls, dto_object: 'interface.DTO') -> 'Proposition':
        raise NotImplementedError

    @classmethod
    def build_from_command(cls, cmd: 'InitierPropositionCommand'):  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def initier_proposition(
        cls,
        cmd: 'InitierPropositionCommand',
        formation_id: 'FormationIdentity',
        proposition_repository: 'IPropositionRepository',
    ) -> 'Proposition':
        return Proposition(
            entity_id=PropositionIdentityBuilder.build(),
            matricule_candidat=cmd.matricule_candidat,
            formation_id=formation_id,
            reference=proposition_repository.recuperer_reference_suivante(),
            motivations=cmd.motivations,
            moyens_decouverte_formation=[
                ChoixMoyensDecouverteFormation[moyen] for moyen in cmd.moyens_decouverte_formation
            ],
            autre_moyen_decouverte_formation=cmd.autre_moyen_decouverte_formation,
            marque_d_interet=cmd.marque_d_interet,
        )
