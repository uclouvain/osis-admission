##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.domain.builder.formation_identity import (
    FormationIdentityBuilder,
)
from admission.ddd.admission.domain.service.i_historique import IHistorique
from admission.ddd.admission.domain.service.i_maximum_propositions import (
    IMaximumPropositionsAutorisees,
)
from admission.ddd.admission.formation_generale.commands import (
    InitierPropositionCommand,
)
from admission.ddd.admission.formation_generale.domain.builder.proposition_builder import (
    PropositionBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.formation_generale.domain.service.i_formation import (
    IFormationGeneraleTranslator,
)
from admission.ddd.admission.formation_generale.repository.i_proposition import (
    IPropositionRepository,
)
from ddd.logic.reference.domain.service.i_bourse import IBourseTranslator


def initier_proposition(
    cmd: 'InitierPropositionCommand',
    proposition_repository: 'IPropositionRepository',
    formation_translator: 'IFormationGeneraleTranslator',
    bourse_translator: 'IBourseTranslator',
    maximum_propositions_service: 'IMaximumPropositionsAutorisees',
    historique: 'IHistorique',
) -> 'PropositionIdentity':
    # GIVEN
    formation_id = FormationIdentityBuilder.build(sigle=cmd.sigle_formation, annee=cmd.annee_formation)
    formation = formation_translator.get(formation_id)
    maximum_propositions_service.verifier_nombre_propositions_en_cours(cmd.matricule_candidat)
    bourses_ids = bourse_translator.search(
        [
            scholarship
            for scholarship in [cmd.bourse_internationale, cmd.bourse_erasmus_mundus, cmd.bourse_double_diplome]
            if scholarship
        ]
    )

    # WHEN
    proposition = PropositionBuilder().initier_proposition(
        cmd=cmd,
        proposition_repository=proposition_repository,
        formation_id=formation.entity_id,
        bourses_ids=bourses_ids,
    )

    # THEN
    proposition_repository.save(proposition)
    historique.historiser_initiation(proposition)

    return proposition.entity_id
