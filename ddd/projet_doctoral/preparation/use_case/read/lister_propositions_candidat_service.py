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

from admission.ddd.projet_doctoral.preparation.commands import ListerPropositionsCandidatQuery
from admission.ddd.projet_doctoral.preparation.dtos import PropositionCandidatDTO
from admission.ddd.projet_doctoral.preparation.repository.i_proposition import IPropositionRepository


def lister_propositions_candidat(
        cmd: 'ListerPropositionsCandidatQuery',
        proposition_repository: 'IPropositionRepository',
) -> List['PropositionCandidatDTO']:
    dtos = proposition_repository.search_dto(matricule_candidat=cmd.matricule_candidat)
    return [
        PropositionCandidatDTO(
            uuid=dto.uuid,
            reference=dto.reference,
            type_admission=dto.type_admission,
            sigle_doctorat=dto.sigle_doctorat,
            intitule_doctorat_fr=dto.intitule_doctorat_fr,
            intitule_doctorat_en=dto.intitule_doctorat_en,
            matricule_candidat=dto.matricule_candidat,
            prenom_candidat=dto.prenom_candidat,
            nom_candidat=dto.nom_candidat,
            code_secteur_formation=dto.code_secteur_formation,
            intitule_secteur_formation=dto.intitule_secteur_formation,
            commission_proximite=dto.commission_proximite,
            creee_le=dto.creee_le,
            statut=dto.statut,
        )
        for dto in dtos
    ]
