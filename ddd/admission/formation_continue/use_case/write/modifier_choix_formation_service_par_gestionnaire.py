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

from admission.ddd.admission.domain.builder.formation_identity import FormationIdentityBuilder
from admission.ddd.admission.formation_continue.commands import ModifierChoixFormationParGestionnaireCommand
from admission.ddd.admission.formation_continue.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_continue.domain.service.i_formation import IFormationContinueTranslator
from admission.ddd.admission.formation_continue.events import FormationDuDossierAdmissionFCModifieeEvent
from admission.ddd.admission.formation_continue.repository.i_proposition import IPropositionRepository


def modifier_choix_formation_par_gestionnaire(
    message_bus,
    cmd: 'ModifierChoixFormationParGestionnaireCommand',
    proposition_repository: 'IPropositionRepository',
    formation_translator: 'IFormationContinueTranslator',
) -> 'PropositionIdentity':
    # GIVEN
    formation_id = FormationIdentityBuilder.build(sigle=cmd.sigle_formation, annee=cmd.annee_formation)
    formation = formation_translator.get(formation_id)
    proposition = proposition_repository.get(PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition))

    # WHEN
    proposition.modifier_choix_formation_par_gestionnaire(
        formation_id=formation.entity_id,
        reponses_questions_specifiques=cmd.reponses_questions_specifiques,
        motivations=cmd.motivations,
        moyens_decouverte_formation=cmd.moyens_decouverte_formation,
        autre_moyen_decouverte_formation=cmd.autre_moyen_decouverte_formation,
        marque_d_interet=cmd.marque_d_interet,
        gestionnaire=cmd.gestionnaire,
    )

    # THEN
    proposition_repository.save(proposition)
    message_bus.publish(
        FormationDuDossierAdmissionFCModifieeEvent(
            entity_id=proposition.entity_id,
            matricule=proposition.matricule_candidat,
        )
    )
    return proposition.entity_id
