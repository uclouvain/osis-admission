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
from typing import Optional

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class ProfilCandidatDTO(interface.DTO):

    # Identification
    nom: Optional[str] = ''
    prenom: Optional[str] = ''
    genre: Optional[str] = ''
    nationalite: Optional[str] = ''
    nom_pays_nationalite: Optional[str] = ''
    date_naissance: Optional[datetime.date] = None

    # Coordonnees
    pays: Optional[str] = ''
    nom_pays: Optional[str] = ''
    code_postal: Optional[str] = ''
    ville: Optional[str] = ''
    rue: Optional[str] = ''
    numero_rue: Optional[str] = ''
    boite_postale: Optional[str] = ''

    @classmethod
    def from_dict(cls, dict_profile, nom_pays_nationalite, nom_pays_adresse):
        identification = dict_profile.get('identification', {})
        coordinates = dict_profile.get('coordinates', {})
        return ProfilCandidatDTO(
            nom=identification.get('last_name'),
            prenom=identification.get('first_name'),
            genre=identification.get('gender'),
            nationalite=identification.get('country_of_citizenship'),
            nom_pays_nationalite=nom_pays_nationalite,
            date_naissance=identification.get('birth_date'),
            pays=coordinates.get('country'),
            nom_pays=nom_pays_adresse,
            code_postal=coordinates.get('postal_code'),
            ville=coordinates.get('city'),
            rue=coordinates.get('street'),
            numero_rue=coordinates.get('street_number'),
            boite_postale=coordinates.get('postal_box'),
        )
