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
from functools import partial

from admission.ddd.admission.formation_generale.commands import *
from admission.ddd.admission.formation_generale.use_case.read import *
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.formation_generale.use_case.write import *
from admission.infrastructure.admission.domain.service.bourse import BourseTranslator
from admission.infrastructure.admission.formation_generale.domain.service.formation import FormationGeneraleTranslator
from admission.infrastructure.admission.formation_generale.repository.proposition import PropositionRepository

COMMAND_HANDLERS = {
    RechercherFormationGeneraleQuery: partial(
        rechercher_formations,
        formation_generale_translator=FormationGeneraleTranslator(),
        annee_inscription_formation_translator=AnneeInscriptionFormationTranslator(),
    ),
    InitierPropositionCommand: partial(
        initier_proposition,
        proposition_repository=PropositionRepository(),
        formation_translator=FormationGeneraleTranslator(),
        bourse_translator=BourseTranslator(),
    ),
    ListerPropositionsCandidatQuery: partial(
        lister_propositions_candidat,
        proposition_repository=PropositionRepository(),
    ),
    RecupererPropositionQuery: partial(
        recuperer_proposition,
        proposition_repository=PropositionRepository(),
    ),
    ModifierChoixFormationCommand: partial(
        modifier_choix_formation,
        proposition_repository=PropositionRepository(),
        formation_translator=FormationGeneraleTranslator(),
        bourse_translator=BourseTranslator(),
    ),
}
