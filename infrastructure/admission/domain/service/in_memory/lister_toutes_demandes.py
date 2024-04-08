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
from typing import Optional, List, Dict

from admission.ddd.admission.doctorat.preparation.dtos import PropositionDTO as PropositionDoctoraleDTO
from admission.ddd.admission.domain.service.i_filtrer_toutes_demandes import IListerToutesDemandes
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO
from admission.ddd.admission.formation_continue.dtos import PropositionDTO as PropositionContinueDTO
from admission.ddd.admission.formation_generale.dtos import PropositionDTO as PropositionGeneraleDTO
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository as PropositionDoctoraleInMemoryRepository,
)
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository as PropositionContinueInMemoryRepository,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository as PropositionGeneraleInMemoryRepository,
)
from admission.views import PaginatedList


class ListerToutesDemandesInMemory(IListerToutesDemandes):
    @classmethod
    def filtrer(
        cls,
        annee_academique: Optional[int] = None,
        numero: Optional[int] = None,
        noma: Optional[str] = '',
        matricule_candidat: Optional[str] = '',
        etats: Optional[List[str]] = None,
        type: Optional[str] = '',
        site_inscription: Optional[str] = '',
        entites: Optional[List[str]] = None,
        types_formation: Optional[List[str]] = None,
        formation: Optional[str] = '',
        bourse_internationale: Optional[str] = '',
        bourse_erasmus_mundus: Optional[str] = '',
        bourse_double_diplomation: Optional[str] = '',
        demandeur: Optional[str] = '',
        tri_inverse: bool = False,
        champ_tri: Optional[str] = None,
        page: Optional[int] = None,
        taille_page: Optional[int] = None,
        mode_filtres_etats_checklist: Optional[str] = '',
        filtres_etats_checklist: Optional[Dict[str, List[str]]] = '',
    ) -> PaginatedList[DemandeRechercheDTO]:

        result = PaginatedList()

        for proposition in PropositionGeneraleInMemoryRepository.search_dto(matricule_candidat=matricule_candidat):
            result.append(cls._load_from_general_proposition(proposition))

        for proposition in PropositionContinueInMemoryRepository.search_dto(matricule_candidat=matricule_candidat):
            result.append(cls._load_from_continuing_proposition(proposition))

        for proposition in PropositionDoctoraleInMemoryRepository.search_dto(matricule_candidat=matricule_candidat):
            result.append(cls._load_from_doctorate_proposition(proposition))

        result.total_count = len(result)

        return result

    @classmethod
    def _load_from_general_proposition(cls, proposition: PropositionGeneraleDTO):
        return DemandeRechercheDTO(
            uuid=proposition.uuid,
            numero_demande=proposition.reference,
            nom_candidat=proposition.nom_candidat,
            prenom_candidat=proposition.prenom_candidat,
            noma_candidat=proposition.matricule_candidat,
            plusieurs_demandes=True,
            sigle_formation=proposition.formation.sigle,
            code_formation=proposition.formation.code,
            intitule_formation=proposition.formation.intitule,
            type_formation=proposition.formation.type,
            lieu_formation=proposition.formation.campus.nom,
            annee_formation=proposition.formation.annee,
            annee_calculee=proposition.annee_calculee,
            nationalite_candidat='',
            nationalite_ue_candidat=None,
            vip=any(
                [
                    proposition.bourse_erasmus_mundus,
                    proposition.bourse_internationale,
                    proposition.bourse_double_diplome,
                ]
            ),
            etat_demande=proposition.statut,
            type_demande='',
            derniere_modification_le=proposition.modifiee_le,
            derniere_modification_par='',
            derniere_modification_par_candidat=False,
            dernieres_vues_par=[],
            date_confirmation=proposition.soumise_le,
            est_premiere_annee=None,
            poursuite_de_cycle='',
        )

    @classmethod
    def _load_from_doctorate_proposition(cls, proposition: PropositionDoctoraleDTO):
        return DemandeRechercheDTO(
            uuid=proposition.uuid,
            numero_demande=proposition.reference,
            nom_candidat=proposition.nom_candidat,
            prenom_candidat=proposition.prenom_candidat,
            noma_candidat=proposition.matricule_candidat,
            plusieurs_demandes=True,
            sigle_formation=proposition.doctorat.sigle,
            code_formation=proposition.doctorat.sigle,
            intitule_formation=proposition.doctorat.intitule,
            type_formation=proposition.doctorat.type,
            lieu_formation=proposition.doctorat.campus,
            annee_formation=proposition.doctorat.annee,
            annee_calculee=proposition.annee_calculee,
            nationalite_candidat=proposition.nationalite_candidat,
            nationalite_ue_candidat=None,
            vip=any([proposition.bourse_recherche]),
            etat_demande=proposition.statut,
            type_demande=proposition.type_admission,
            derniere_modification_le=proposition.modifiee_le,
            derniere_modification_par='',
            derniere_modification_par_candidat=False,
            dernieres_vues_par=[],
            date_confirmation=proposition.soumise_le,
            est_premiere_annee=None,
            poursuite_de_cycle='',
        )

    @classmethod
    def _load_from_continuing_proposition(cls, proposition: PropositionContinueDTO):
        return DemandeRechercheDTO(
            uuid=proposition.uuid,
            numero_demande=proposition.reference,
            nom_candidat=proposition.nom_candidat,
            prenom_candidat=proposition.prenom_candidat,
            noma_candidat=proposition.matricule_candidat,
            plusieurs_demandes=True,
            sigle_formation=proposition.formation.sigle,
            code_formation=proposition.formation.sigle,
            intitule_formation=proposition.formation.intitule,
            type_formation=proposition.formation.type,
            lieu_formation=proposition.formation.campus.nom,
            annee_formation=proposition.formation.annee,
            nationalite_candidat=proposition.pays_nationalite_candidat,
            nationalite_ue_candidat=proposition.pays_nationalite_ue_candidat,
            vip=False,
            etat_demande=proposition.statut,
            type_demande='',
            derniere_modification_le=proposition.modifiee_le,
            derniere_modification_par='',
            derniere_modification_par_candidat=False,
            dernieres_vues_par=[],
            date_confirmation=proposition.soumise_le,
            est_premiere_annee=None,
            poursuite_de_cycle='',
            annee_calculee=proposition.annee_calculee,
        )
