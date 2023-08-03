##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
from admission.ddd.admission.domain.service.i_unites_enseignement_translator import IUnitesEnseignementTranslator
from admission.ddd.admission.formation_generale.commands import RecupererPropositionGestionnaireQuery
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.dtos.proposition import PropositionGestionnaireDTO
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository


def recuperer_proposition_gestionnaire(
    cmd: 'RecupererPropositionGestionnaireQuery',
    proposition_repository: 'IPropositionRepository',
    unites_enseignement_translator: 'IUnitesEnseignementTranslator',
) -> 'PropositionGestionnaireDTO':
    return proposition_repository.get_dto_for_gestionnaire(
        entity_id=PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition),
        unites_enseignement_translator=unites_enseignement_translator,
    )
