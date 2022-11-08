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

from admission.ddd.admission.doctorat.validation.commands import *
from admission.ddd.admission.doctorat.validation.use_case.read import *
from admission.ddd.admission.doctorat.validation.use_case.write import *
from admission.infrastructure.parcours_doctoral.epreuve_confirmation.repository.in_memory.epreuve_confirmation import (
    EpreuveConfirmationInMemoryRepository,
)
from admission.infrastructure.parcours_doctoral.repository.in_memory.doctorat import DoctoratInMemoryRepository
from .repository.in_memory.demande import DemandeInMemoryRepository
from ..preparation.repository.in_memory.proposition import PropositionInMemoryRepository

_proposition_repository = PropositionInMemoryRepository()
_demande_repository = DemandeInMemoryRepository()
_epreuve_confirmation_repository = EpreuveConfirmationInMemoryRepository()
_doctorat_repository = DoctoratInMemoryRepository()


COMMAND_HANDLERS = {
    FiltrerDemandesQuery: lambda msg_bus, cmd: filtrer_demandes(
        cmd,
        proposition_repository=_proposition_repository,
        demande_repository=_demande_repository,
    ),
    RecupererDemandeQuery: lambda msg_bus, cmd: recuperer_demande(
        cmd,
        demande_repository=_demande_repository,
    ),
    RefuserDemandeCddCommand: lambda msg_bus, cmd: refuser_demande_cdd(
        cmd,
        demande_repository=_demande_repository,
    ),
    ApprouverDemandeCddCommand: lambda msg_bus, cmd: approuver_demande_cdd(
        cmd,
        demande_repository=_demande_repository,
        proposition_repository=_proposition_repository,
        epreuve_confirmation_repository=_epreuve_confirmation_repository,
        doctorat_repository=_doctorat_repository,
    ),
}
