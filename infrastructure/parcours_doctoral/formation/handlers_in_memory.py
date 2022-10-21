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

from admission.ddd.parcours_doctoral.formation.commands import *
from admission.ddd.parcours_doctoral.formation.use_case.write import *
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from .domain.service.in_memory.notification import NotificationInMemory
from .repository.in_memory.activite import ActiviteInMemoryRepository
from ..repository.in_memory.doctorat import DoctoratInMemoryRepository

COMMAND_HANDLERS = {
    SupprimerActiviteCommand: partial(
        supprimer_activite,
        activite_repository=ActiviteInMemoryRepository(),
    ),
    SoumettreActivitesCommand: partial(
        soumettre_activites,
        activite_repository=ActiviteInMemoryRepository(),
        doctorat_repository=DoctoratInMemoryRepository(),
        groupe_de_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        notification=NotificationInMemory(),
    ),
    DonnerAvisSurActiviteCommand: partial(
        donner_avis_sur_activite,
        activite_repository=ActiviteInMemoryRepository(),
    ),
    AccepterActivitesCommand: partial(
        accepter_activites,
        activite_repository=ActiviteInMemoryRepository(),
        doctorat_repository=DoctoratInMemoryRepository(),
        notification=NotificationInMemory(),
    ),
    RefuserActiviteCommand: partial(
        refuser_activite,
        activite_repository=ActiviteInMemoryRepository(),
        doctorat_repository=DoctoratInMemoryRepository(),
        notification=NotificationInMemory(),
    ),
    RevenirSurStatutActiviteCommand: partial(
        revenir_sur_statut_activite,
        activite_repository=ActiviteInMemoryRepository(),
    ),
}
