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

from admission.ddd.admission.formation_continue.commands import ListerDemandesQuery
from admission.ddd.admission.formation_continue.domain.service.i_lister_demandes import IListerDemandesService
from admission.ddd.admission.formation_continue.dtos.liste import DemandeRechercheDTO


def lister_demandes(
    cmd: 'ListerDemandesQuery',
    lister_demandes_service: 'IListerDemandesService',
) -> 'List[DemandeRechercheDTO]':
    return lister_demandes_service.lister(
        annee_academique=cmd.annee_academique,
        edition=cmd.edition,
        numero=cmd.numero,
        matricule_candidat=cmd.matricule_candidat,
        etats=cmd.etats,
        facultes=cmd.facultes,
        types_formation=cmd.types_formation,
        sigles_formations=cmd.sigles_formations,
        inscription_requise=cmd.inscription_requise,
        paye=cmd.paye,
        marque_d_interet=cmd.marque_d_interet,
        mode_filtres_etats_checklist=cmd.mode_filtres_etats_checklist,
        filtres_etats_checklist=cmd.filtres_etats_checklist,
        demandeur=cmd.demandeur,
        champ_tri=cmd.champ_tri,
        tri_inverse=cmd.tri_inverse,
        page=cmd.page,
        taille_page=cmd.taille_page,
    )
