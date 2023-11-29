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
from admission.ddd.admission.domain.builder.titre_acces_selectionnable_builder import TitreAccesSelectionnableBuilder
from admission.ddd.admission.domain.model.titre_acces_selectionnable import TitreAccesSelectionnableIdentity
from admission.ddd.admission.domain.repository.i_titre_acces_selectionnable import ITitreAccesSelectionnableRepository
from admission.ddd.admission.formation_generale.commands import SpecifierExperienceEnTantQueTitreAccesCommand


def specifier_experience_en_tant_que_titre_acces(
    cmd: 'SpecifierExperienceEnTantQueTitreAccesCommand',
    titre_acces_selectionnable_repository: 'ITitreAccesSelectionnableRepository',
) -> 'TitreAccesSelectionnableIdentity':
    titre_acces = TitreAccesSelectionnableBuilder.build_from_command(cmd=cmd)
    titre_acces_selectionnable_repository.save(titre_acces)

    return titre_acces.entity_id
