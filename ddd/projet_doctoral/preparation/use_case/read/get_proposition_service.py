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
from admission.ddd.projet_doctoral.preparation.commands import GetPropositionCommand
from admission.ddd.projet_doctoral.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.projet_doctoral.preparation.domain.service.i_secteur_ucl import ISecteurUclTranslator
from admission.ddd.projet_doctoral.preparation.domain.service.get_proposition_dto import GetPropositionDTODomainService
from admission.ddd.projet_doctoral.preparation.dtos import PropositionDTO
from admission.ddd.projet_doctoral.preparation.repository.i_proposition import IPropositionRepository


def get_proposition(
    cmd: 'GetPropositionCommand',
    proposition_repository: 'IPropositionRepository',
    doctorat_translator: 'IDoctoratTranslator',
    secteur_ucl_translator: 'ISecteurUclTranslator',
) -> 'PropositionDTO':
    return GetPropositionDTODomainService().get(
        uuid_proposition=cmd.uuid_proposition,
        repository=proposition_repository,
        doctorat_translator=doctorat_translator,
        secteur_ucl_translator=secteur_ucl_translator,
    )
