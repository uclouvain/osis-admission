# ##############################################################################
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
# ##############################################################################
from typing import Optional, List

from admission.ddd.admission.domain.model.proposition_fusion_personne import PropositionFusionPersonneIdentity
from admission.ddd.admission.dtos.proposition_fusion_personne import PropositionFusionPersonneDTO
from admission.ddd.admission.repository.i_proposition_fusion_personne import IPropositionPersonneFusionRepository
from base.models.person import Person
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from osis_common.utils.models import get_object_or_none
from reference.models.country import Country


class PropositionPersonneFusionInMemoryRepository(IPropositionPersonneFusionRepository):
    @classmethod
    def initialiser(
            cls,
            global_id: str,
            nom: str,
            prenom: str,
            autres_prenoms: str,
            date_naissance: str,
            lieu_naissance: str,
            email: str,
            genre: str,
            etat_civil: str,
            nationalite: str,
            numero_national: str,
            numero_carte_id: str,
            numero_passeport: str,
            dernier_noma_connu: str,
            expiration_carte_id: str,
            educational_curex_ids: List[str],
            professional_curex_ids: List[str],
    ) -> PropositionFusionPersonneIdentity:
        return PropositionFusionPersonneIdentity(uuid="uuid")

    @classmethod
    def get(cls, global_id: str) -> Optional[PropositionFusionPersonneDTO]:
        return None

    @classmethod
    def defaire(cls, global_id: str) -> PropositionFusionPersonneIdentity:
        return PropositionFusionPersonneIdentity(uuid="uuid")
