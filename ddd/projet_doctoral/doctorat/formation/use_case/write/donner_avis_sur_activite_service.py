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

from admission.ddd.projet_doctoral.doctorat.formation.builder.activite_identity_builder import ActiviteIdentityBuilder
from admission.ddd.projet_doctoral.doctorat.formation.commands import DonnerAvisSurActiviteCommand
from admission.ddd.projet_doctoral.doctorat.formation.domain.model.activite import ActiviteIdentity
from admission.ddd.projet_doctoral.doctorat.formation.repository.i_activite import IActiviteRepository


def donner_avis_sur_activite(
    cmd: 'DonnerAvisSurActiviteCommand',
    activite_repository: 'IActiviteRepository',
) -> 'ActiviteIdentity':
    # GIVEN
    activite_id = ActiviteIdentityBuilder.build_from_uuid(cmd.activite_uuid)
    activite = activite_repository.get(activite_id)

    # WHEN

    # THEN
    activite.donner_avis_promoteur_reference(cmd.approbation, cmd.commentaire)
    activite_repository.save(activite)

    return activite_id
