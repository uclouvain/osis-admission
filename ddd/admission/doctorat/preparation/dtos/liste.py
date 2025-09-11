# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class DemandeRechercheDTO(interface.DTO):
    uuid: str
    numero_demande: str
    etat_demande: str

    nom_candidat: str
    prenom_candidat: str
    noma_candidat: str
    sigle_formation: str
    code_formation: str
    intitule_formation: str

    decision_fac: str
    decision_sic: str

    signatures_completees: bool

    date_confirmation: Optional[datetime.datetime]

    derniere_modification_le: datetime.datetime
    type_admission: str

    cotutelle: Optional[bool]

    code_pays_nationalite_candidat: str = ''
    nom_pays_nationalite_candidat: str = ''

    code_bourse: str = ''

    prenom_auteur_derniere_modification: str = ''
    nom_auteur_derniere_modification: str = ''

    @property
    def formation(self) -> str:
        return f'{self.sigle_formation} - {self.intitule_formation}'

    @property
    def candidat(self) -> str:
        noma = f' ({self.noma_candidat})' if self.noma_candidat else ''
        return f'{self.nom_candidat}, {self.prenom_candidat}{noma}'

    @property
    def derniere_modification_par(self) -> str:
        return f'{self.nom_auteur_derniere_modification}, {self.prenom_auteur_derniere_modification[:1]}'
