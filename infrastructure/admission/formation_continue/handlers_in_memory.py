##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.formation_continue.commands import *
from admission.ddd.admission.formation_continue.use_case.read import *
from admission.ddd.admission.formation_continue.use_case.write import *
from admission.infrastructure.admission.domain.service.in_memory.annee_inscription_formation import (
    AnneeInscriptionFormationInMemoryTranslator,
)
from admission.infrastructure.admission.domain.service.in_memory.titres_acces import TitresAccesInMemory
from admission.infrastructure.admission.formation_continue.domain.service.in_memory.formation import (
    FormationContinueInMemoryTranslator,
)
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)

_proposition_repository = PropositionInMemoryRepository()
_formation_continue_translator = FormationContinueInMemoryTranslator()
_annee_inscription_formation_translator = AnneeInscriptionFormationInMemoryTranslator()
_titres_acces = TitresAccesInMemory()


COMMAND_HANDLERS = {
    RechercherFormationContinueQuery: lambda msg_bus, cmd: rechercher_formations(
        cmd,
        formation_continue_translator=_formation_continue_translator,
        annee_inscription_formation_translator=_annee_inscription_formation_translator,
    ),
    InitierPropositionCommand: lambda msg_bus, cmd: initier_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_formation_continue_translator,
    ),
    ListerPropositionsCandidatQuery: lambda msg_bus, cmd: lister_propositions_candidat(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    RecupererPropositionQuery: lambda msg_bus, cmd: recuperer_proposition(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    ModifierChoixFormationCommand: lambda msg_bus, cmd: modifier_choix_formation(
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_formation_continue_translator,
    ),
    SupprimerPropositionCommand: lambda msg_bus, cmd: supprimer_proposition(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    VerifierPropositionCommand: lambda msg_bus, cmd: verifier_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_formation_continue_translator,
        titres_acces=_titres_acces,
    ),
}
