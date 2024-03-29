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
from admission.ddd.admission.shared_kernel.email_destinataire.queries import RecupererInformationsDestinataireQuery
from admission.ddd.admission.shared_kernel.email_destinataire.use_case.read.recuperer_informations_destinataire_service\
    import recuperer_informations_destinataire
from admission.ddd.admission.use_case.read import *
from admission.infrastructure.admission.domain.service.lister_toutes_demandes import ListerToutesDemandes
from admission.infrastructure.admission.shared_kernel.email_destinataire.repository.email_destinataire import \
    EmailDestinataireRepository

COMMAND_HANDLERS = {
    ListerToutesDemandesQuery: lambda msg_bus, cmd: lister_demandes(
        cmd,
        lister_toutes_demandes_service=ListerToutesDemandes(),
    ),
    RecupererInformationsDestinataireQuery: lambda msg_bus, query: recuperer_informations_destinataire(
        query,
        email_destinataire_repository=EmailDestinataireRepository()
    ),
}
