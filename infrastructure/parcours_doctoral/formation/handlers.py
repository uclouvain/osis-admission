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

from admission.ddd.parcours_doctoral.formation.commands import *
from admission.ddd.parcours_doctoral.formation.use_case.write import *
from admission.infrastructure.admission.doctorat.preparation.repository.groupe_de_supervision import (
    GroupeDeSupervisionRepository,
)
from admission.infrastructure.parcours_doctoral.formation.domain.service.notification import Notification
from admission.infrastructure.parcours_doctoral.formation.repository.activite import ActiviteRepository
from admission.infrastructure.parcours_doctoral.repository.doctorat import DoctoratRepository

COMMAND_HANDLERS = {
    SupprimerActiviteCommand: lambda msg_bus, cmd: supprimer_activite(
        cmd,
        activite_repository=ActiviteRepository(),
    ),
    SoumettreActivitesCommand: lambda msg_bus, cmd: soumettre_activites(
        cmd,
        activite_repository=ActiviteRepository(),
        doctorat_repository=DoctoratRepository(),
        groupe_de_supervision_repository=GroupeDeSupervisionRepository(),
        notification=Notification(),
    ),
    DonnerAvisSurActiviteCommand: lambda msg_bus, cmd: donner_avis_sur_activite(
        cmd,
        activite_repository=ActiviteRepository(),
    ),
    AccepterActivitesCommand: lambda msg_bus, cmd: accepter_activites(
        cmd,
        activite_repository=ActiviteRepository(),
        doctorat_repository=DoctoratRepository(),
        notification=Notification(),
    ),
    RefuserActiviteCommand: lambda msg_bus, cmd: refuser_activite(
        cmd,
        activite_repository=ActiviteRepository(),
        doctorat_repository=DoctoratRepository(),
        notification=Notification(),
    ),
    RevenirSurStatutActiviteCommand: lambda msg_bus, cmd: revenir_sur_statut_activite(
        cmd,
        activite_repository=ActiviteRepository(),
    ),
}
