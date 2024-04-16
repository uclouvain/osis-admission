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
import datetime
from typing import List, Optional

import attr

from osis_common.ddd import interface
from osis_profile import PLUS_5_ISO_CODES, BE_ISO_CODE


@attr.dataclass(frozen=True, slots=True)
class IdentificationDTO(interface.DTO):
    matricule: str

    nom: str
    prenom: str
    autres_prenoms: str
    date_naissance: Optional[datetime.date]
    annee_naissance: Optional[int]
    pays_nationalite: str
    pays_nationalite_europeen: Optional[bool]
    nom_pays_nationalite: str
    sexe: str
    genre: str
    photo_identite: List[str]
    pays_naissance: str
    nom_pays_naissance: str
    lieu_naissance: str
    etat_civil: str
    pays_residence: str

    carte_identite: List[str]
    passeport: List[str]
    numero_registre_national_belge: str
    numero_carte_identite: str
    numero_passeport: str
    date_expiration_carte_identite: Optional[datetime.date]
    date_expiration_passeport: Optional[datetime.date]

    langue_contact: str
    nom_langue_contact: str
    email: str

    annee_derniere_inscription_ucl: Optional[int]
    noma_derniere_inscription_ucl: str

    @property
    def est_concerne_par_visa(self):
        """
        Retourne si le candidat est concerné par la question du visa.
        Prérequis: la demande concernée doit être une formation générale.
        """
        return bool(
            self.pays_nationalite
            and self.pays_nationalite_europeen is False
            and self.pays_nationalite not in PLUS_5_ISO_CODES
            and self.pays_residence
            and self.pays_residence != BE_ISO_CODE
        )
