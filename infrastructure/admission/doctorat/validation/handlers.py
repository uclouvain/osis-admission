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
from admission.infrastructure.parcours_doctoral.epreuve_confirmation.repository.epreuve_confirmation import (
    EpreuveConfirmationRepository,
)
from admission.infrastructure.parcours_doctoral.repository.doctorat import DoctoratRepository
from .repository.demande import DemandeRepository
from ..preparation.repository.proposition import PropositionRepository

COMMAND_HANDLERS = {
    FiltrerDemandesQuery: lambda msg_bus, cmd: filtrer_demandes(
        cmd,
        proposition_repository=PropositionRepository(),
        demande_repository=DemandeRepository(),
    ),
    RecupererDemandeQuery: lambda msg_bus, cmd: recuperer_demande(
        cmd,
        demande_repository=DemandeRepository(),
    ),
    RefuserDemandeCddCommand: lambda msg_bus, cmd: refuser_demande_cdd(
        cmd,
        demande_repository=DemandeRepository(),
    ),
    ApprouverDemandeCddCommand: lambda msg_bus, cmd: approuver_demande_cdd(
        cmd,
        demande_repository=DemandeRepository(),
        proposition_repository=PropositionRepository(),
        epreuve_confirmation_repository=EpreuveConfirmationRepository(),
        doctorat_repository=DoctoratRepository(),
    ),
}
