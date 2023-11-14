##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class ProfilCandidat(interface.ValueObject):

    # Identification
    nom: Optional[str] = ''
    prenom: Optional[str] = ''
    genre: Optional[str] = ''
    nationalite: Optional[str] = ''

    # Coordonnees
    pays: Optional[str] = ''
    code_postal: Optional[str] = ''
    ville: Optional[str] = ''
    rue: Optional[str] = ''
    numero_rue: Optional[str] = ''
    boite_postale: Optional[str] = ''

    def to_dict(self):
        return {
            'identification': {
                'first_name': self.prenom,
                'last_name': self.nom,
                'gender': self.genre,
                'country_of_citizenship': self.nationalite,
            },
            'coordinates': {
                'country': self.pays,
                'postal_code': self.code_postal,
                'city': self.ville,
                'street': self.rue,
                'street_number': self.numero_rue,
                'postal_box': self.boite_postale,
            },
        }

    @classmethod
    def from_dict(cls, dict_profile):
        identification = dict_profile.get('identification', {})
        coordinates = dict_profile.get('coordinates', {})
        return ProfilCandidat(
            nom=identification.get('last_name'),
            prenom=identification.get('first_name'),
            genre=identification.get('gender'),
            nationalite=identification.get('country_of_citizenship'),
            pays=coordinates.get('country'),
            code_postal=coordinates.get('postal_code'),
            ville=coordinates.get('city'),
            rue=coordinates.get('street'),
            numero_rue=coordinates.get('street_number'),
            boite_postale=coordinates.get('postal_box'),
        )
