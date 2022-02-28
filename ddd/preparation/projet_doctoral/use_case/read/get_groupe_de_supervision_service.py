##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.preparation.projet_doctoral.commands import GetGroupeDeSupervisionCommand
from admission.ddd.preparation.projet_doctoral.domain.service.groupe_de_supervision_dto import GroupeDeSupervisionDto
from admission.ddd.preparation.projet_doctoral.domain.service.i_membre_CA import IMembreCATranslator
from admission.ddd.preparation.projet_doctoral.domain.service.i_promoteur import IPromoteurTranslator
from admission.ddd.preparation.projet_doctoral.dtos import GroupeDeSupervisionDTO
from admission.ddd.preparation.projet_doctoral.repository.i_groupe_de_supervision import IGroupeDeSupervisionRepository


def get_groupe_de_supervision(
    cmd: 'GetGroupeDeSupervisionCommand',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    promoteur_translator: 'IPromoteurTranslator',
    membre_ca_translator: 'IMembreCATranslator',
) -> 'GroupeDeSupervisionDTO':
    return GroupeDeSupervisionDto().get(
        uuid_proposition=cmd.uuid_proposition,
        repository=groupe_supervision_repository,
        promoteur_translator=promoteur_translator,
        membre_ca_translator=membre_ca_translator,
    )
