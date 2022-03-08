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
from admission.ddd.projet_doctoral.validation.builder.demande_identity import DemandeIdentityBuilder
from admission.ddd.projet_doctoral.validation.commands import ApprouverDemandeCddCommand
from admission.ddd.projet_doctoral.validation.domain.model.demande import DemandeIdentity
from admission.ddd.projet_doctoral.validation.repository.i_demande import IDemandeRepository


def approuver_demande_cdd(
    cmd: 'ApprouverDemandeCddCommand',
    demande_repository: 'IDemandeRepository',
) -> 'DemandeIdentity':
    # GIVEN
    demande = demande_repository.get(entity_id=DemandeIdentityBuilder.build_from_uuid(cmd.uuid))

    # WHEN
    demande.approuver_cdd()

    # THEN
    demande_repository.save(demande)

    return demande.entity_id
