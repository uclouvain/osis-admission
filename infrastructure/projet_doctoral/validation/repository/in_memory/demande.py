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
from datetime import datetime
from typing import List, Optional

from admission.ddd.projet_doctoral.validation.domain.model.demande import Demande, DemandeIdentity
from admission.ddd.projet_doctoral.validation.dtos import DemandeDTO, DemandeRechercheDTO
from admission.ddd.projet_doctoral.validation.repository.i_demande import IDemandeRepository
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


class DemandeInMemoryRepository(InMemoryGenericRepository, IDemandeRepository):
    entities: List[Demande] = list()
    dtos: List[DemandeRechercheDTO] = list()

    @classmethod
    def search_dto(
        cls,
        numero: Optional[str] = '',
        etat_cdd: Optional[str] = '',
        etat_sic: Optional[str] = '',
        nom_prenom_email: Optional[str] = '',
        nationalite: Optional[str] = '',
        type: Optional[str] = '',
        commission_proximite: Optional[str] = '',
        annee_academique: Optional[str] = '',
        sigle_formation: Optional[str] = '',
        financement: Optional[str] = '',
        matricule_promoteur: Optional[str] = None,
        cotutelle: Optional[bool] = None,
        date_pre_admission_debut: Optional[datetime] = None,
        date_pre_admission_fin: Optional[datetime] = None,
        **kwargs,
    ) -> List['DemandeRechercheDTO']:
        matching: List[DemandeRechercheDTO] = []
        for dto in cls.dtos:
            if numero and dto.numero_demande == numero:
                matching.append(dto)
                # TODO
        return matching

    @classmethod
    def search(cls, entity_ids: Optional[List['DemandeIdentity']] = None, **kwargs) -> List['Demande']:
        return [e for e in cls.entities if e.entity_id in entity_ids]

    @classmethod
    def reset(cls):
        cls.entities = []

    def get_dto(cls, entity_id) -> DemandeDTO:
        pass
