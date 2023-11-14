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
from typing import List

from admission.ddd.parcours_doctoral.builder.doctorat_identity import DoctoratIdentityBuilder
from admission.ddd.parcours_doctoral.formation.commands import AccepterActivitesCommand
from admission.ddd.parcours_doctoral.formation.domain.model.activite import ActiviteIdentity
from admission.ddd.parcours_doctoral.formation.domain.service.accepter_activites import AccepterActivites
from admission.ddd.parcours_doctoral.formation.domain.service.i_notification import INotification
from admission.ddd.parcours_doctoral.formation.repository.i_activite import IActiviteRepository
from admission.ddd.parcours_doctoral.repository.i_doctorat import IDoctoratRepository


def accepter_activites(
    cmd: 'AccepterActivitesCommand',
    activite_repository: 'IActiviteRepository',
    doctorat_repository: 'IDoctoratRepository',
    notification: 'INotification',
) -> List['ActiviteIdentity']:
    # GIVEN
    doctorat_id = DoctoratIdentityBuilder.build_from_uuid(cmd.doctorat_uuid)
    doctorat = doctorat_repository.get(doctorat_id)
    activites = AccepterActivites.verifier(cmd.activite_uuids, activite_repository)

    # WHEN

    # THEN
    entity_ids = AccepterActivites.accepter(activites, activite_repository)
    notification.notifier_validation_au_candidat(doctorat, activites)

    return entity_ids
