##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.parcours_doctoral.commands import *
from admission.ddd.parcours_doctoral.use_case.read import *
from admission.ddd.parcours_doctoral.use_case.write import *
from admission.infrastructure.parcours_doctoral.domain.service.in_memory.historique import HistoriqueInMemory
from admission.infrastructure.parcours_doctoral.domain.service.in_memory.notification import NotificationInMemory
from admission.infrastructure.parcours_doctoral.repository.in_memory.doctorat import DoctoratInMemoryRepository

_doctorat_repository = DoctoratInMemoryRepository()
_notification = NotificationInMemory()
_historique = HistoriqueInMemory()


COMMAND_HANDLERS = {
    RecupererAdmissionDoctoratQuery: lambda msg_bus, cmd: recuperer_admission_doctorat(
        cmd,
        doctorat_repository=_doctorat_repository,
    ),
    EnvoyerMessageDoctorantCommand: lambda msg_bus, cmd: envoyer_message_au_doctorant(
        cmd,
        doctorat_repository=_doctorat_repository,
        notification=_notification,
        historique=_historique,
    ),
}
