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
from typing import List, Optional

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class IdentificationDTO(interface.DTO):
    matricule: str

    nom: Optional[str]
    prenom: Optional[str]
    date_naissance: Optional[datetime.date]
    annee_naissance: Optional[int]
    pays_nationalite: Optional[str]
    sexe: Optional[str]
    genre: Optional[str]
    photo_identite: List[str]
    pays_naissance: Optional[str]
    lieu_naissance: Optional[str]
    etat_civil: Optional[str]
    pays_residence: Optional[str]

    carte_identite: List[str]
    passeport: List[str]
    numero_registre_national_belge: Optional[str]
    numero_carte_identite: Optional[str]
    numero_passeport: Optional[str]

    langue_contact: Optional[str]
    email: Optional[str]

    annee_derniere_inscription_ucl: Optional[int]
    noma_derniere_inscription_ucl: Optional[str]
