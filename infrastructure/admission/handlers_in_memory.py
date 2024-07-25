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
from admission.ddd.admission.commands import *
from admission.ddd.admission.shared_kernel.email_destinataire.queries import RecupererInformationsDestinataireQuery
from admission.ddd.admission.shared_kernel.email_destinataire.use_case.read import *
from admission.ddd.admission.use_case.read import *
from admission.infrastructure.admission.domain.service.in_memory.lister_toutes_demandes import (
    ListerToutesDemandesInMemory,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator

from admission.infrastructure.admission.repository.in_memory.emplacement_document import (
    emplacement_document_in_memory_repository,
)
from admission.infrastructure.admission.shared_kernel.email_destinataire.repository.in_memory import (
    EmailDestinataireInMemoryRepository,
)

_emplacement_document_repository = emplacement_document_in_memory_repository
_profil_candidat_translator = ProfilCandidatInMemoryTranslator()


COMMAND_HANDLERS = {
    ListerToutesDemandesQuery: lambda msg_bus, cmd: lister_demandes(
        cmd,
        lister_toutes_demandes_service=ListerToutesDemandesInMemory(),
    ),
    RecupererInformationsDestinataireQuery: lambda msg_bus, query: recuperer_informations_destinataire(
        query,
        email_destinataire_repository=EmailDestinataireInMemoryRepository(),
    ),
    RecupererEtudesSecondairesQuery: lambda msg_bus, query: recuperer_etudes_secondaires(
        query,
        profil_candidat_translator=_profil_candidat_translator,
    ),
    RecupererExperienceAcademiqueQuery: lambda msg_bus, query: recuperer_experience_academique(
        query,
        profil_candidat_translator=_profil_candidat_translator,
    ),
    RecupererExperienceNonAcademiqueQuery: lambda msg_bus, query: recuperer_experience_non_academique(
        query,
        profil_candidat_translator=_profil_candidat_translator,
    ),
    RecupererConnaissancesLanguesQuery: lambda msg_bus, query: recuperer_connaissances_langues(
        query,
        profil_candidat_translator=_profil_candidat_translator,
    ),
}
