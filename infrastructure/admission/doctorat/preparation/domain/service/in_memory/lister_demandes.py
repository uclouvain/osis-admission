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
import datetime
from typing import Optional, List, Dict

from admission.ddd.admission.doctorat.preparation.domain.service.i_lister_demandes import IListerDemandesService
from admission.ddd.admission.doctorat.preparation.dtos.liste import DemandeRechercheDTO
from admission.views import PaginatedList


class ListerDemandesInMemoryService(IListerDemandesService):
    @classmethod
    def lister(
        cls,
        annee_academique: Optional[int] = None,
        numero: Optional[int] = None,
        matricule_candidat: Optional[str] = '',
        nationalite: Optional[str] = '',
        etats: Optional[List[str]] = None,
        type: Optional[str] = '',
        cdds: Optional[List[str]] = None,
        commission_proximite: Optional[str] = '',
        sigles_formations: Optional[List[str]] = None,
        matricule_promoteur: Optional[str] = '',
        type_financement: Optional[str] = '',
        bourse_recherche: Optional[str] = '',
        cotutelle: Optional[bool] = None,
        date_soumission_debut: Optional[datetime.date] = None,
        date_soumission_fin: Optional[datetime.date] = None,
        mode_filtres_etats_checklist: Optional[str] = '',
        filtres_etats_checklist: Optional[Dict[str, List[str]]] = None,
        demandeur: Optional[str] = '',
        fnrs_fria_fresh: Optional[bool] = None,
        tri_inverse: bool = False,
        champ_tri: Optional[str] = None,
        page: Optional[int] = None,
        taille_page: Optional[int] = None,
    ) -> PaginatedList[DemandeRechercheDTO]:
        return PaginatedList(id_attribute='uuid')
