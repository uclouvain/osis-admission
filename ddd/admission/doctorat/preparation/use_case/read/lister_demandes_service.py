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
from typing import List

from admission.ddd.admission.doctorat.preparation.commands import ListerDemandesQuery
from admission.ddd.admission.doctorat.preparation.domain.service.i_lister_demandes import IListerDemandesService
from admission.ddd.admission.doctorat.preparation.dtos.liste import DemandeRechercheDTO


def lister_demandes(
    cmd: 'ListerDemandesQuery',
    lister_demandes_service: 'IListerDemandesService',
) -> List['DemandeRechercheDTO']:
    return lister_demandes_service.lister(
        annee_academique=cmd.annee_academique,
        numero=cmd.numero,
        matricule_candidat=cmd.matricule_candidat,
        nationalite=cmd.nationalite,
        etats=cmd.etats,
        type=cmd.type,
        cdds=cmd.cdds,
        commission_proximite=cmd.commission_proximite,
        sigles_formations=cmd.sigles_formations,
        matricule_promoteur=cmd.matricule_promoteur,
        type_financement=cmd.type_financement,
        bourse_recherche=cmd.bourse_recherche,
        cotutelle=cmd.cotutelle,
        date_soumission_debut=cmd.date_soumission_debut,
        date_soumission_fin=cmd.date_soumission_fin,
        mode_filtres_etats_checklist=cmd.mode_filtres_etats_checklist,
        filtres_etats_checklist=cmd.filtres_etats_checklist,
        demandeur=cmd.demandeur,
        tri_inverse=cmd.tri_inverse,
        champ_tri=cmd.champ_tri,
        page=cmd.page,
        taille_page=cmd.taille_page,
    )
