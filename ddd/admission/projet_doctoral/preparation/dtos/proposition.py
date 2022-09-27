##############################################################################
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
##############################################################################
import datetime
from typing import Dict, List, Optional
from uuid import UUID

import attr

from .doctorat import DoctoratDTO
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class PropositionDTO(interface.DTO):
    uuid: str
    type_admission: str
    reference: str
    justification: Optional[str]
    doctorat: DoctoratDTO
    code_secteur_formation: str
    intitule_secteur_formation: str
    commission_proximite: Optional[str]
    type_financement: Optional[str]
    type_contrat_travail: Optional[str]
    eft: Optional[int]
    bourse_recherche: Optional[str]
    bourse_date_debut: Optional[datetime.date]
    bourse_date_fin: Optional[datetime.date]
    bourse_preuve: List[str]
    duree_prevue: Optional[int]
    temps_consacre: Optional[int]
    titre_projet: Optional[str]
    resume_projet: Optional[str]
    documents_projet: List[str]
    graphe_gantt: List[str]
    proposition_programme_doctoral: List[str]
    projet_formation_complementaire: List[str]
    lettres_recommandation: List[str]
    langue_redaction_these: str
    institut_these: Optional[UUID]
    lieu_these: str
    doctorat_deja_realise: str
    institution: Optional[str]
    domaine_these: str
    date_soutenance: Optional[datetime.date]
    raison_non_soutenue: Optional[str]
    statut: str
    fiche_archive_signatures_envoyees: List[str]
    matricule_candidat: str
    prenom_candidat: str
    nom_candidat: str
    nationalite_candidat: str
    creee_le: datetime.datetime
    modifiee_le: datetime.datetime
    erreurs: List[Dict[str, str]]
