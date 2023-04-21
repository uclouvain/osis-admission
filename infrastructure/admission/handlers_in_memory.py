##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.commands import *
from admission.ddd.admission.use_case.read import *
from admission.ddd.admission.use_case.write import *
from admission.infrastructure.admission.domain.service.in_memory.lister_toutes_demandes import (
    ListerToutesDemandesInMemory,
)

from admission.infrastructure.admission.repository.emplacement_document import EmplacementDocumentRepository

_emplacement_document_repository = EmplacementDocumentRepository()


COMMAND_HANDLERS = {
    ListerToutesDemandesQuery: lambda msg_bus, cmd: lister_demandes(
        cmd,
        lister_toutes_demandes_service=ListerToutesDemandesInMemory(),
    ),
    DeposerDocumentLibreParGestionnaireCommand: lambda msg_bus, cmd: deposer_document_libre_par_gestionnaire(
        cmd,
        emplacement_document_repository=_emplacement_document_repository,
    ),
    ReclamerDocumentLibreCommand: lambda msg_bus, cmd: reclamer_document_libre(
        cmd,
        emplacement_document_repository=_emplacement_document_repository,
    ),
    ReclamerDocumentCommand: lambda msg_bus, cmd: reclamer_document(
        cmd,
        emplacement_document_repository=_emplacement_document_repository,
    ),
    AnnulerReclamationDocumentCommand: lambda msg_bus, cmd: annuler_reclamation_document(
        cmd,
        emplacement_document_repository=_emplacement_document_repository,
    ),
}
