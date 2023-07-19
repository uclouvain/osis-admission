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
from admission.ddd.admission.domain.builder.formation_identity import FormationIdentityBuilder
from admission.ddd.admission.domain.service.i_bourse import IBourseTranslator
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.commands import (
    ModifierChoixFormationCommand,
    ModifierChecklistChoixFormationCommand,
)
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.enums import PoursuiteDeCycle
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.i_formation import IFormationGeneraleTranslator
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository


def modifier_checklist_choix_formation(
    cmd: 'ModifierChecklistChoixFormationCommand',
    proposition_repository: 'IPropositionRepository',
    formation_translator: 'IFormationGeneraleTranslator',
) -> 'PropositionIdentity':
    # GIVEN
    formation_id = FormationIdentityBuilder.build(sigle=cmd.sigle_formation, annee=cmd.annee_formation)
    formation = formation_translator.get(formation_id)
    proposition = proposition_repository.get(PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition))

    # WHEN
    proposition.modifier_checklist_choix_formation(
        type_demande=TypeDemande[cmd.type_demande],
        formation_id=formation.entity_id,
        poursuite_de_cycle=PoursuiteDeCycle[cmd.poursuite_de_cycle],
    )

    # THEN
    proposition_repository.save(proposition)

    return proposition.entity_id
