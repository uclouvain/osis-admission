# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from typing import List

from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.doctorat.preparation.commands import RecupererElementsConfirmationQuery
from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.domain.service.i_elements_confirmation import ElementConfirmation, IElementsConfirmation
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator


def recuperer_elements_confirmation(
    cmd: 'RecupererElementsConfirmationQuery',
    proposition_repository: 'IPropositionRepository',
    element_confirmation: 'IElementsConfirmation',
    formation_translator: 'IDoctoratTranslator',
    profil_candidat_translator: 'IProfilCandidatTranslator',
) -> List['ElementConfirmation']:
    # GIVEN
    entity_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=entity_id)

    # THEN
    return element_confirmation.recuperer(
        proposition=proposition,
        formation_translator=formation_translator,
        profil_candidat_translator=profil_candidat_translator,
    )
