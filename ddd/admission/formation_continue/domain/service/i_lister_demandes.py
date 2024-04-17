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
from abc import abstractmethod
from typing import Optional, List, Dict

from admission.ddd.admission.formation_continue.dtos.liste import DemandeRechercheDTO
from admission.views import PaginatedList
from osis_common.ddd import interface


class IListerDemandesService(interface.DomainService):
    @classmethod
    @abstractmethod
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
        demandeur: Optional[str] = '',
        tri_inverse: bool = False,
        champ_tri: Optional[str] = None,
        page: Optional[int] = None,
        taille_page: Optional[int] = None,
    ) -> PaginatedList[DemandeRechercheDTO]:
        raise NotImplementedError
