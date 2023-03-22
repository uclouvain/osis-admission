# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime
from typing import Optional, List

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class VisualiseurAdmissionDTO(interface.DTO):
    nom: str
    prenom: str
    date: datetime.datetime


@attr.dataclass(frozen=True, slots=True)
class DemandeRechercheDTO(interface.DTO):
    uuid: str
    numero_demande: str
    nom_candidat: str
    prenom_candidat: str
    noma_candidat: Optional[str]
    plusieurs_demandes: bool
    sigle_formation: str
    sigle_partiel_formation: str
    intitule_formation: str
    type_formation: str
    lieu_formation: str
    nationalite_candidat: str
    nationalite_ue_candidat: Optional[bool]
    vip: bool
    etat_demande: str
    type_demande: str
    derniere_modification_le: datetime.datetime
    derniere_modification_par: str
    derniere_modification_par_candidat: bool
    dernieres_vues_par: List[VisualiseurAdmissionDTO]
    date_confirmation: Optional[datetime.datetime]
