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

from admission.ddd.admission.commands import ListerToutesDemandesQuery
from admission.ddd.admission.domain.service.i_filtrer_toutes_demandes import IListerToutesDemandes
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO


def lister_demandes(
    cmd: 'ListerToutesDemandesQuery',
    lister_toutes_demandes_service: 'IListerToutesDemandes',
) -> 'List[DemandeRechercheDTO]':
    return lister_toutes_demandes_service.filtrer(
        annee_academique=cmd.annee_academique,
        numero=cmd.numero,
        noma=cmd.noma,
        matricule_candidat=cmd.matricule_candidat,
        etats=cmd.etats,
        type=cmd.type,
        site_inscription=cmd.site_inscription,
        entites=cmd.entites,
        types_formation=cmd.types_formation,
        formation=cmd.formation,
        bourse_internationale=cmd.bourse_internationale,
        bourse_erasmus_mundus=cmd.bourse_erasmus_mundus,
        bourse_double_diplomation=cmd.bourse_double_diplomation,
        quarantaine=cmd.quarantaine,
        demandeur=cmd.demandeur,
        tri_inverse=cmd.tri_inverse,
        champ_tri=cmd.champ_tri,
        page=cmd.page,
        taille_page=cmd.taille_page,
        mode_filtres_etats_checklist=cmd.mode_filtres_etats_checklist,
        filtres_etats_checklist=cmd.filtres_etats_checklist,
        injection_en_erreur=cmd.injection_en_erreur,
    )
