# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.formation_continue.domain.service.i_lister_demandes import IListerDemandesService
from admission.ddd.admission.formation_continue.dtos import PropositionDTO
from admission.ddd.admission.formation_continue.dtos.liste import DemandeRechercheDTO
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.views import PaginatedList


class ListerDemandesInMemory(IListerDemandesService):
    @classmethod
    def lister(
        cls,
        annee_academique: Optional[int] = None,
        edition: Optional[str] = '',
        numero: Optional[int] = None,
        matricule_candidat: Optional[str] = '',
        etats: Optional[List[str]] = None,
        facultes: Optional[List[str]] = None,
        types_formation: Optional[List[str]] = None,
        sigles_formations: Optional[List] = None,
        inscription_requise: Optional[bool] = None,
        paye: Optional[bool] = None,
        marque_d_interet: Optional[bool] = None,
        demandeur: Optional[str] = '',
        tri_inverse: bool = False,
        champ_tri: Optional[str] = None,
        page: Optional[int] = None,
        taille_page: Optional[int] = None,
    ) -> PaginatedList[DemandeRechercheDTO]:

        result = PaginatedList()

        for proposition in PropositionInMemoryRepository.search_dto(matricule_candidat=matricule_candidat):
            result.append(cls._load_from_continuing_proposition(proposition))

        result.total_count = len(result)

        return result

    @classmethod
    def _load_from_continuing_proposition(cls, proposition: PropositionDTO):
        return DemandeRechercheDTO(
            uuid=proposition.uuid,
            numero_demande=proposition.reference,
            nom_candidat=proposition.nom_candidat,
            prenom_candidat=proposition.prenom_candidat,
            noma_candidat=proposition.matricule_candidat,
            courriel_candidat='',
            sigle_formation=proposition.formation.sigle,
            code_formation=proposition.formation.code,
            intitule_formation=proposition.formation.intitule,
            inscription_au_role_obligatoire=None,
            edition=proposition.edition,
            sigle_faculte=proposition.formation.sigle_entite_gestion,
            paye=proposition.en_ordre_de_paiement,
            etat_demande=proposition.statut,
            etat_epc='',
            date_confirmation=proposition.soumise_le,
            derniere_modification_le=proposition.modifiee_le,
            derniere_modification_par='',
        )
