# ##############################################################################
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
# ##############################################################################
from admission.ddd.admission.doctorat.validation.builder.demande_identity import DemandeIdentityBuilder
from admission.ddd.admission.doctorat.validation.commands import RecupererDemandeQuery
from admission.ddd.admission.doctorat.validation.domain.service.demande import DemandeService
from admission.ddd.admission.doctorat.validation.dtos import DemandeDTO
from admission.ddd.admission.doctorat.validation.repository.i_demande import IDemandeRepository


def recuperer_demande(
    cmd: 'RecupererDemandeQuery',
    demande_repository: 'IDemandeRepository',
) -> DemandeDTO:
    # GIVEN
    demande_id = DemandeIdentityBuilder.build_from_uuid(cmd.uuid)
    return DemandeService.recuperer(
        demande_id,
        demande_repository,
    )
