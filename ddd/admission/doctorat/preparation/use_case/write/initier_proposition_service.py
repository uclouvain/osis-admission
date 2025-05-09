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
from admission.ddd.admission.doctorat.preparation.builder.proposition_builder import (
    PropositionBuilder,
)
from admission.ddd.admission.doctorat.preparation.commands import (
    InitierPropositionCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import (
    IDoctoratTranslator,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import (
    IHistorique,
)
from admission.ddd.admission.doctorat.preparation.domain.service.parcours_doctoral import (
    ParcoursDoctoralTranslator,
)
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import (
    IPropositionRepository,
)
from admission.ddd.admission.domain.service.i_maximum_propositions import (
    IMaximumPropositionsAutorisees,
)
from infrastructure.utils import MessageBus


def initier_proposition(
    message_bus: 'MessageBus',
    cmd: 'InitierPropositionCommand',
    proposition_repository: 'IPropositionRepository',
    doctorat_translator: 'IDoctoratTranslator',
    historique: 'IHistorique',
    maximum_propositions_service: 'IMaximumPropositionsAutorisees',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
) -> 'PropositionIdentity':
    # GIVEN
    maximum_propositions_service.verifier_nombre_propositions_en_cours(cmd.matricule_candidat)

    parcours_doctoral_pre_admission_associee = ParcoursDoctoralTranslator.recuperer(
        message_bus=message_bus,
        uuid_proposition=cmd.pre_admission_associee,
    )

    # WHEN
    proposition = PropositionBuilder().initier_proposition(
        cmd=cmd,
        doctorat_translator=doctorat_translator,
        proposition_repository=proposition_repository,
        parcours_doctoral_pre_admission_associee=parcours_doctoral_pre_admission_associee,
    )

    # THEN
    proposition_repository.save(
        proposition,
        dupliquer_documents=bool(cmd.pre_admission_associee),
    )

    groupe_supervision_repository.initialize_supervision_group_from_proposition(
        uuid_proposition_originale=cmd.pre_admission_associee,
        nouvelle_proposition=proposition,
    )

    historique.historiser_initiation(proposition.entity_id, cmd.matricule_candidat)

    return proposition.entity_id
