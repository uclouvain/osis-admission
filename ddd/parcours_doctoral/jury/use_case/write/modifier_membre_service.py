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

from admission.ddd.parcours_doctoral.jury.builder.jury_identity_builder import JuryIdentityBuilder
from admission.ddd.parcours_doctoral.jury.commands import ModifierMembreCommand
from admission.ddd.parcours_doctoral.jury.domain.model.jury import JuryIdentity, MembreJury
from admission.ddd.parcours_doctoral.jury.repository.i_jury import IJuryRepository


def modifier_membre(
    cmd: 'ModifierMembreCommand',
    jury_repository: 'IJuryRepository',
) -> 'JuryIdentity':
    # GIVEN
    membre = MembreJury(
        est_promoteur=None,
        uuid=cmd.uuid_membre,
        matricule=cmd.matricule,
        institution=cmd.institution,
        autre_institution=cmd.autre_institution,
        pays=cmd.pays,
        nom=cmd.nom,
        prenom=cmd.prenom,
        titre=cmd.titre,
        justification_non_docteur=cmd.justification_non_docteur,
        genre=cmd.genre,
        email=cmd.email,
    )
    jury = jury_repository.get(JuryIdentityBuilder.build_from_uuid(cmd.uuid_jury))

    # WHEN

    # THEN
    jury.modifier_membre(membre)
    jury_repository.save(jury)
    return jury.entity_id
