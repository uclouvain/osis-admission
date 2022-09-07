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

from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.commands import *
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.use_case.read import *
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.use_case.write import *
from .domain.service.in_memory.notification import NotificationInMemory
from .repository.in_memory.epreuve_confirmation import EpreuveConfirmationInMemoryRepository
from ..repository.in_memory.doctorat import DoctoratInMemoryRepository

COMMAND_HANDLERS = {
    RecupererEpreuvesConfirmationQuery: partial(
        recuperer_epreuves_confirmation,
        epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
        doctorat_repository=DoctoratInMemoryRepository(),
    ),
    RecupererDerniereEpreuveConfirmationQuery: partial(
        recuperer_derniere_epreuve_confirmation,
        epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
        doctorat_repository=DoctoratInMemoryRepository(),
    ),
    ModifierEpreuveConfirmationParCDDCommand: partial(
        modifier_epreuve_confirmation_par_cdd,
        epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
    ),
    SoumettreEpreuveConfirmationCommand: partial(
        soumettre_epreuve_confirmation,
        doctorat_repository=DoctoratInMemoryRepository(),
        epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
        notification=NotificationInMemory(),
    ),
    CompleterEpreuveConfirmationParPromoteurCommand: partial(
        completer_epreuve_confirmation_par_promoteur,
        epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
    ),
    SoumettreReportDeDateCommand: partial(
        soumettre_report_de_date,
        epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
        notification=NotificationInMemory(),
    ),
    SoumettreAvisProlongationCommand: partial(
        soumettre_avis_prolongation,
        epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
    ),
    ConfirmerReussiteCommand: partial(
        confirmer_reussite,
        epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
        doctorat_repository=DoctoratInMemoryRepository(),
        notification=NotificationInMemory(),
    ),
    ConfirmerEchecCommand: partial(
        confirmer_echec,
        epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
        doctorat_repository=DoctoratInMemoryRepository(),
        notification=NotificationInMemory(),
    ),
    ConfirmerRepassageCommand: partial(
        confirmer_repassage,
        epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
        doctorat_repository=DoctoratInMemoryRepository(),
        notification=NotificationInMemory(),
    ),
    TeleverserAvisRenouvellementMandatRechercheCommand: partial(
        televerser_avis_renouvellement_mandat_recherche,
        epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
    ),
}
