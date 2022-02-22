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

from typing import List

from admission.ddd.validation.projet_doctoral.commands import RechercherDemandeQuery
from admission.ddd.validation.projet_doctoral.dtos import DemandeRechercheDTO
from admission.ddd.validation.projet_doctoral.repository.i_demande import IDemandeRepository


def rechercher_demandes(
    cmd: 'RechercherDemandeQuery',
    demande_repository: 'IDemandeRepository',
) -> 'List[DemandeRechercheDTO]':
    # GIVEN
    return demande_repository.search_dto(
        numero=cmd.numero,
        etat_cdd=cmd.etat_cdd,
        etat_sic=cmd.etat_sic,
        nom_prenom_email=cmd.nom_prenom_email,
        nationalite=cmd.nationalite,
        type=cmd.type,
        commission_proximite=cmd.commission_proximite,
        annee_academique=cmd.annee_academique,
        sigle_formation=cmd.sigle_formation,
        financement=cmd.financement,
        matricule_promoteur=cmd.matricule_promoteur,
        cotutelle=cmd.cotutelle,
        date_pre_admission_debut=cmd.date_pre_admission_debut,
        date_pre_admission_fin=cmd.date_pre_admission_fin,
    )
