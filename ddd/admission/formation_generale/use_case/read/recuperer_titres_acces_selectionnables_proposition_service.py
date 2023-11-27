# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict

from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.repository.i_titre_acces_selectionnable import ITitreAccesSelectionnableRepository
from admission.ddd.admission.dtos.titre_acces_selectionnable import TitreAccesSelectionnableDTO
from admission.ddd.admission.formation_generale.commands import RecupererTitresAccesSelectionnablesPropositionQuery


def recuperer_titres_acces_selectionnables_proposition(
    cmd: 'RecupererTitresAccesSelectionnablesPropositionQuery',
    titre_acces_selectionnable_repository: 'ITitreAccesSelectionnableRepository',
) -> Dict[str, TitreAccesSelectionnableDTO]:
    proposition_identity = PropositionIdentity(uuid=cmd.uuid_proposition)
    return titre_acces_selectionnable_repository.search_dto_by_proposition(proposition_identity=proposition_identity)
