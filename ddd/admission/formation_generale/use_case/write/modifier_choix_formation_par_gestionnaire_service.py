##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.domain.service.i_bourse import IBourseTranslator
from admission.ddd.admission.formation_generale.commands import ModifierChoixFormationParGestionnaireCommand
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.events import FormationDuDossierAdmissionModifieeEvent
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository


def modifier_choix_formation_par_gestionnaire(
    message_bus,
    cmd: 'ModifierChoixFormationParGestionnaireCommand',
    proposition_repository: 'IPropositionRepository',
    bourse_translator: 'IBourseTranslator',
) -> 'PropositionIdentity':
    # GIVEN
    proposition = proposition_repository.get(PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition))
    bourses_ids = bourse_translator.search(
        [
            scholarship
            for scholarship in [cmd.bourse_internationale, cmd.bourse_erasmus_mundus, cmd.bourse_double_diplome]
            if scholarship
        ]
    )

    # WHEN
    proposition.modifier_choix_formation_par_gestionnaire(
        auteur_modification=cmd.gestionnaire,
        bourses_ids=bourses_ids,
        bourse_double_diplome=cmd.bourse_double_diplome,
        bourse_internationale=cmd.bourse_internationale,
        bourse_erasmus_mundus=cmd.bourse_erasmus_mundus,
        reponses_questions_specifiques=cmd.reponses_questions_specifiques,
    )

    # THEN
    proposition_repository.save(proposition)
    message_bus.publish(
        FormationDuDossierAdmissionModifieeEvent(entity_id=proposition.entity_id)
    )
    return proposition.entity_id
