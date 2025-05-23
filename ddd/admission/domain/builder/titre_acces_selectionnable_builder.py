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
from admission.ddd.admission.domain.model.enums.condition_acces import (
    TypeTitreAccesSelectionnable,
)
from admission.ddd.admission.domain.model.titre_acces_selectionnable import (
    TitreAccesSelectionnable,
    TitreAccesSelectionnableIdentity,
)
from admission.ddd.admission.dtos.titre_acces_selectionnable import (
    TitreAccesSelectionnableDTO,
)
from admission.ddd.admission.formation_generale.commands import (
    SpecifierExperienceEnTantQueTitreAccesCommand,
)
from osis_common.ddd import interface


class TitreAccesSelectionnableBuilder(interface.RootEntityBuilder):
    @classmethod
    def build_from_command(cls, cmd: 'SpecifierExperienceEnTantQueTitreAccesCommand') -> 'TitreAccesSelectionnable':
        return TitreAccesSelectionnable(
            entity_id=TitreAccesSelectionnableIdentity(
                uuid_experience=cmd.uuid_experience,
                uuid_proposition=cmd.uuid_proposition,
                type_titre=TypeTitreAccesSelectionnable[cmd.type_experience],
            ),
            selectionne=cmd.selectionne,
            annee=None,
            pays_iso_code='',
            nom='',
        )

    @classmethod
    def build_from_repository_dto(cls, dto_object: 'TitreAccesSelectionnableDTO') -> 'TitreAccesSelectionnable':
        raise NotImplementedError
