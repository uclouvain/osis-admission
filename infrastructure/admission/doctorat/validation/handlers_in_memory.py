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

from admission.ddd.admission.doctorat.validation.commands import *
from admission.ddd.admission.doctorat.validation.use_case.read import *
from admission.ddd.admission.doctorat.validation.use_case.write import *
from admission.infrastructure.parcours_doctoral.epreuve_confirmation.repository.in_memory.epreuve_confirmation import (
    EpreuveConfirmationInMemoryRepository,
)
from admission.infrastructure.parcours_doctoral.repository.in_memory.doctorat import DoctoratInMemoryRepository
from .repository.in_memory.demande import DemandeInMemoryRepository
from ..preparation.repository.in_memory.proposition import PropositionInMemoryRepository

COMMAND_HANDLERS = {
    FiltrerDemandesQuery: partial(
        filtrer_demandes,
        proposition_repository=PropositionInMemoryRepository(),
        demande_repository=DemandeInMemoryRepository(),
    ),
    RecupererDemandeQuery: partial(
        recuperer_demande,
        demande_repository=DemandeInMemoryRepository(),
    ),
    RefuserDemandeCddCommand: partial(
        refuser_demande_cdd,
        demande_repository=DemandeInMemoryRepository(),
    ),
    ApprouverDemandeCddCommand: partial(
        approuver_demande_cdd,
        demande_repository=DemandeInMemoryRepository(),
        proposition_repository=PropositionInMemoryRepository(),
        epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
        doctorat_repository=DoctoratInMemoryRepository(),
    ),
}
