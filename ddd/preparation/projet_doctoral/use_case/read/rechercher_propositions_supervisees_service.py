# ##############################################################################
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
# ##############################################################################
from typing import List

from admission.ddd.preparation.projet_doctoral.commands import SearchPropositionsSuperviseesCommand
from admission.ddd.preparation.projet_doctoral.domain.service.get_proposition_dto import GetPropositionDTODomainService
from admission.ddd.shared_kernel.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.shared_kernel.domain.service.i_secteur_ucl import ISecteurUclTranslator
from admission.ddd.preparation.projet_doctoral.dtos import PropositionCandidatDTO
from admission.ddd.preparation.projet_doctoral.repository.i_groupe_de_supervision import IGroupeDeSupervisionRepository
from admission.ddd.preparation.projet_doctoral.repository.i_proposition import IPropositionRepository
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import IPersonneConnueUclTranslator


def rechercher_propositions_supervisees(
    cmd: 'SearchPropositionsSuperviseesCommand',
    proposition_repository: 'IPropositionRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    doctorat_translator: 'IDoctoratTranslator',
    secteur_ucl_translator: 'ISecteurUclTranslator',
    personne_connue_ucl_translator: 'IPersonneConnueUclTranslator',
) -> List['PropositionCandidatDTO']:
    groupes = groupe_supervision_repository.search(matricule_membre=cmd.matricule_membre)
    propositions = proposition_repository.search(entity_ids=[g.proposition_id for g in groupes])
    return [
        GetPropositionDTODomainService.search_dto(
            proposition,
            doctorat_translator,
            secteur_ucl_translator,
            personne_connue_ucl_translator,
        )
        for proposition in propositions
    ]
